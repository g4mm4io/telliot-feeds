import os
from decimal import *
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import time

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from eth_utils.conversions import to_bytes
from eth_abi import decode_abi
from web3 import Web3

import requests
import json

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

class TWAPLPSpotPriceService(WebPriceService):
    """TWAP Price Service"""
    ABI = """
    [
        {
            "inputs": [],
            "name": "getReserves",
            "outputs": [
            { "internalType": "uint112", "name": "reserve0", "type": "uint112" },
            { "internalType": "uint112", "name": "reserve1", "type": "uint112" },
            {
                "internalType": "uint32",
                "name": "blockTimestampLast",
                "type": "uint32"
            }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "type": "function",
            "stateMutability": "view",
            "payable": false,
            "outputs": [{ "type": "uint256", "name": "", "internalType": "uint256" }],
            "name": "price0CumulativeLast",
            "inputs": [],
            "constant": true
        },
        {
            "type": "function",
            "stateMutability": "view",
            "payable": false,
            "outputs": [{ "type": "uint256", "name": "", "internalType": "uint256" }],
            "name": "price1CumulativeLast",
            "inputs": [],
            "constant": true
        }
    ]
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "TWAP LP Price Service"
        kwargs["url"] = os.getenv("LP_PULSE_NETWORK_URL", "https://rpc.v4.testnet.pulsechain.com")
        kwargs["timeout"] = int(os.getenv('TWAP_TIMESPAN'))

        self.prevPricesPath: Path = Path('./prevPricesCumulative.json') 

        self.contract_addresses: dict[str, str] = self._get_contract_address()
        self.lps_order: dict[str, str] = self._get_lps_order()
        self.max_retries = int(os.getenv('MAX_RETRIES', 5))

        super().__init__(**kwargs)

    def _get_contract_address(self) -> dict[str, str]:
        addrs = {}
        sources_addrs = os.getenv("PLS_ADDR_SOURCES")
        sources = os.getenv("PLS_CURRENCY_SOURCES")
        sources_list = sources.split(',')
        sources_addr_list = sources_addrs.split(',')

        if len(sources_list) != len(sources_addr_list):
            raise Exception('PLS_CURRENCY_SOURCES and PLS_ADDR_SOURCES must have the same length')

        for i,s in enumerate(sources_list):
            addrs[s] = Web3.toChecksumAddress(sources_addr_list[i])
        return addrs

    def _get_lps_order(self) -> dict[str, str]:
        lps_order = {}
        sources_list = os.getenv("PLS_CURRENCY_SOURCES").split(',')
        order_list = os.getenv("PLS_LPS_ORDER").split(',')
        if len(sources_list) != len(order_list):
            raise Exception('PLS_CURRENCY_SOURCES and PLS_ADDR_SOURCES must have the same length')
        for i,s in enumerate(sources_list):
            lps_order[s] = order_list[i].lower()
        return lps_order
    
    def _callGetReserves(self, contract_address: str):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                w3 = Web3(Web3.HTTPProvider(self.url, request_kwargs={'timeout': self.timeout}))
                contract = w3.eth.contract(address=contract_address, abi=self.ABI)
                return contract.functions.getReserves().call()
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"""
                    Error calling RPC 'getReserves'
                    {'' if retry_count == self.max_retries else 'Trying again...'}
                    """
                )
        raise Exception(f"Failed to call RPC 'getReserves', address {contract_address}")

    def _callPricesCumulativeLast(self, contract_address: str) -> tuple[int]:
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                w3 = Web3(Web3.HTTPProvider(self.url, request_kwargs={'timeout': self.timeout}))
                contract = w3.eth.contract(address=contract_address, abi=self.ABI)
                price0CumulativeLast = contract.functions.price0CumulativeLast().call()
                price1CumulativeLast = contract.functions.price1CumulativeLast().call()
                _, _, _blockTimestampLast = self._callGetReserves(contract_address)
                return price0CumulativeLast, price1CumulativeLast, _blockTimestampLast
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"""
                    Error calling RPC in '_callPricesCumulativeLast' method
                    {'' if retry_count == self.max_retries else 'Trying again...'}
                    """
                )
                logger.error(e)
        raise Exception(f"Failed to call RPC in '_callPricesCumulativeLast' method, address {contract_address}")
    
    def _get_pair_json_key(self, currency: str) -> str:
        token0, token1 = self.lps_order[currency].split('/')
        return f"{token0.upper()}/{token1.upper()}"
    
    def _read_cumulative_prices_json(self) -> dict:
        if self.prevPricesPath.exists():
            return json.loads(self.prevPricesPath.read_text())
        return {}

    def _update_cumulative_prices_json(
        self,
        price0CumulativeLast: int,
        price1CumulativeLast: int,
        blockTimestampLast: int,
        key: str
    ) -> None:
        json_data = self._read_cumulative_prices_json()

        json_data[key] = {
            'price0CumulativeLast': str(price0CumulativeLast),
            'price1CumulativeLast': str(price1CumulativeLast),
            'blockTimestampLast': str(blockTimestampLast)
        }
        self.prevPricesPath.write_text(json.dumps(json_data))
        logger.info(f'Entry {key} updated in Cumulative prices JSON')

    def get_prev_prices_cumulative(self, currency: str) -> tuple[int]:
        key = self._get_pair_json_key(currency)

        json_data = self._read_cumulative_prices_json()

        if key not in json_data.keys():
            address = self.contract_addresses[currency]
            price0CumulativeLast, price1CumulativeLast, _blockTimestampLast = self._callPricesCumulativeLast(address)
            self._update_cumulative_prices_json(
                price0CumulativeLast,
                price1CumulativeLast,
                _blockTimestampLast,
                key
            )
            logger.info(f'Cumulative prices JSON {key} data initialized')
            return price0CumulativeLast, price1CumulativeLast, _blockTimestampLast

        logger.info(f'Cumulative prices JSON {key} data found')
        try:
            prevPrice0CumulativeLast = int(json_data[key]['price0CumulativeLast'])
            prevPrice1CumulativeLast = int(json_data[key]['price1CumulativeLast'])
            prevBlockTimestampLast = int(json_data[key]['blockTimestampLast'])
            return prevPrice0CumulativeLast, prevPrice1CumulativeLast, prevBlockTimestampLast
        except (json.decoder.JSONDecodeError, ValueError) as e: 
            logger.error(f"""
            Error while reading Cumulative Prices JSON file:
            {self.prevPricesPath.resolve()}
            You can manually delete the file and restart the service to automatically initialize it

            The expected JSON format is:
            {{
                "WPLS/DAI": {{
                    "price0CumulativeLast": "123456789",
                    "price1CumulativeLast": "123456789",
                    "blockTimestampLast": "123456789"
                }},
                ...
            }}
            """)
            logger.error(e)

    def _get_current_block_timestamp(self):
        w3 = Web3(Web3.HTTPProvider(self.url))
        block = w3.eth.getBlock("latest")
        timestamp = block.timestamp
        return timestamp % 2**32
    
    def _calculate_cumulative_price(
        self, address: str,
        price0Cumulative: int,
        price1Cumulative: int,
        blockTimestampLast: int
    ) -> tuple[int]:
        currentTimesamp = self._get_current_block_timestamp()
        timeElapsed = currentTimesamp - blockTimestampLast
        reserve0, reserve1, _ = self._callGetReserves(address)
        fixed_point_fraction0 = (reserve1 / reserve0) * (2 ** 112)
        fixed_point_fraction1 = (reserve0 / reserve1) * (2 ** 112)
        price0Cumulative += int(fixed_point_fraction0) * timeElapsed
        price1Cumulative += int(fixed_point_fraction1) * timeElapsed
        return price0Cumulative, price1Cumulative, currentTimesamp

    def get_currentPrices(
        self,
        prevPrice0CumulativeLast: int,
        prevPrice1CumulativeLast: int,
        prevBlockTimestampLast: int,
        currency: str
    ) -> tuple[int]:
        address = self.contract_addresses[currency]

        price0CumulativeLast, price1CumulativeLast, blockTimestampLast = self._callPricesCumulativeLast(address)

        if (blockTimestampLast <= prevBlockTimestampLast):
            logger.info(
                f"""
                BlockTimestampLast <= prevBlockTimestampLast:
                currentBlockTimestampLas / prevBlockTimestampLast: {blockTimestampLast} / {prevBlockTimestampLast}
                Updating cumulative prices according to current block time stamp
                """
            )
            price0CumulativeLast, price1CumulativeLast, blockTimestampLast = self._calculate_cumulative_price(
                address,
                price0CumulativeLast,
                price1CumulativeLast,
                blockTimestampLast
            )
            logger.info(
                f"""
                Updated cumulative prices:
                currentBlockTimestampLas / prevBlockTimestampLast: {blockTimestampLast} / {prevBlockTimestampLast}    
                currentPrice0 / prevPrice0: {price0CumulativeLast} / {prevPrice0CumulativeLast}
                currentPrice1 / prevPrice1: {price1CumulativeLast} / {prevPrice1CumulativeLast}
                """
            )
        return price0CumulativeLast, price1CumulativeLast, blockTimestampLast
        
    def calculate_twap(
        self,
        currentPrice: int,
        prevPrice: int,
        blockTimestampLast: int,
        prevBlockTimestampLast: int,
    ) -> float:
        sub = (currentPrice - prevPrice) / 2**112
        logger.info(
            f"""
            Calculated TWAP price:
            Where numerator = ({currentPrice} - {prevPrice}) / 2**112
            ({sub}) / ({blockTimestampLast} - {prevBlockTimestampLast})
            """
        )
        return (sub) / (blockTimestampLast - prevBlockTimestampLast)

    def _get_total_value_locked(self, currency: str):
        reserve0, reserve1, _ = self._callGetReserves(self.contract_addresses[currency])
        token0, _ = self.lps_order[currency].split('/')
        if "pls" not in token0.strip():
            reserve0, reserve1 = reserve1, reserve0
        vl0 = ((1e18 * reserve1) / (reserve0 + 1e18)) * reserve0 # value locked token0 without fees
        vl1 = ((1e18 * reserve0) / (reserve1 + 1e18)) * reserve1 # value locked token0 without fees
        tvl = vl0 + vl1 # total value locked of the pool
        return tvl

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface"""

        asset = asset.lower()
        currency = currency.lower()

        if currency not in ["usdc", "dai", "usdt"]:
            logger.error(f"Currency not supported: {currency}")
            return None, None

        try:
            prevPrice0CumulativeLast, prevPrice1CumulativeLast, prevBlockTimestampLast = self.get_prev_prices_cumulative(
                currency
            )

            price0CumulativeLast, price1CumulativeLast, blockTimestampLast = self.get_currentPrices(
                prevPrice0CumulativeLast,
                prevPrice1CumulativeLast,
                prevBlockTimestampLast,
                currency
            )

            try:
                token0, _ = self.lps_order[currency].split('/')
                if "pls" in token0.strip():
                    logger.info("Using price0CumulativeLast")
                    twap = self.calculate_twap(
                        price0CumulativeLast,
                        prevPrice0CumulativeLast,
                        blockTimestampLast,
                        prevBlockTimestampLast,
                    )
                else:
                    logger.info("Using price1CumulativeLast")
                    twap = self.calculate_twap(
                        price1CumulativeLast,
                        prevPrice1CumulativeLast,
                        blockTimestampLast,
                        prevBlockTimestampLast,
                    )
            except KeyError as e:
                logger.error(f'currency {currency} not found in the provided PLS_CURRENCY_SOURCES')
                logger.error(e)

            self._update_cumulative_prices_json(
                price0CumulativeLast,
                price1CumulativeLast,
                blockTimestampLast,
                self._get_pair_json_key(currency)
            )

            price = float(twap)
            if currency == 'usdc' or currency == 'usdt':
                price = price * 1e12

            logger.info(f"""
            TWAP LP price for {asset}-{currency}: {price}
            LP contract address: {self.contract_addresses[currency]}
            """)

            weight = self._get_total_value_locked(currency)

            return price, datetime_now_utc(), float(weight)
        except Exception as e:
            logger.error(e)
            return None, None

@dataclass
class TWAPLPSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: TWAPLPSpotPriceService = field(default_factory=TWAPLPSpotPriceService, init=False)
