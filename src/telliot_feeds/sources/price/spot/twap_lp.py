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
        kwargs["timeout"] = 10.0

        self.prevPricesPath: Path = Path('./prevPricesCumulative.json') 

        self.contract_addresses: dict[str, str] = self._get_contract_address()
        self.lps_order: dict[str, str] = self._get_lps_order()
        self.contract = None

        super().__init__(**kwargs)

    def _initialize_lp_contract(self, currency: str):
        contract_address = self.contract_addresses[currency]
        w3 = Web3(Web3.HTTPProvider(self.url, request_kwargs={'timeout': self.timeout}))
        contract = w3.eth.contract(address=contract_address, abi=self.ABI)
        self.contract = contract

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
    
    def _callGetReserves(self):
        return self.contract.functions.getReserves().call()

    def _callPricesCumulativeLast(self) -> tuple[int]:
        price0CumulativeLast = self.contract.functions.price0CumulativeLast().call()
        price1CumulativeLast = self.contract.functions.price1CumulativeLast().call()
        _, _, _blockTimestampLast = self._callGetReserves()
        return price0CumulativeLast, price1CumulativeLast, _blockTimestampLast
    
    def _write_prices_as_json(self, currentPrice0: int, currentPrice1: int, blockTimestamp: int, log_msg: str) -> None:
        json_data = {
            'price0CumulativeLast': str(currentPrice0),
            'price1CumulativeLast': str(currentPrice1),
            'blockTimestampLast': str(blockTimestamp)
        }
        self.prevPricesPath.write_text(json.dumps(json_data))
        logger.info(log_msg)

    def get_prev_prices_cumulative(self) -> tuple[int]:
        if not self.prevPricesPath.exists():
            price0CumulativeLast, price1CumulativeLast, _blockTimestampLast = self._callPricesCumulativeLast()
            self._write_prices_as_json(
                price0CumulativeLast, price1CumulativeLast, _blockTimestampLast, "Cumulative prices JSON data initialized"
            )
            return price0CumulativeLast, price1CumulativeLast, _blockTimestampLast
    
        logger.info('Cumulative prices JSON data found')
        try:
            prevPricesCumulative = json.loads(self.prevPricesPath.read_text())
            prevPrice0CumulativeLast = int(prevPricesCumulative['price0CumulativeLast'])
            prevPrice1CumulativeLast = int(prevPricesCumulative['price1CumulativeLast'])
            prevBlockTimestampLast = int(prevPricesCumulative['blockTimestampLast'])
            return prevPrice0CumulativeLast, prevPrice1CumulativeLast, prevBlockTimestampLast
        except json.decoder.JSONDecodeError:
            print('Error while reading json file, please check it')
    
    def poll_to_get_currentPrices(
        self,
        prevPrice0CumulativeLast: int,
        prevPrice1CumulativeLast: int,
        prevBlockTimestampLast: int
    ) -> tuple[int]:
        polling_interval = 60
        while True:
            price0CumulativeLast, price1CumulativeLast, blockTimestampLast = self._callPricesCumulativeLast()
            if (price0CumulativeLast == prevPrice0CumulativeLast or
                price1CumulativeLast == prevPrice1CumulativeLast or
                blockTimestampLast == prevBlockTimestampLast):
                    logger.warning(
                        f'pricesCumulativeLast or blockTimestampLast not updated yet, waiting {polling_interval} seconds...'
                    )
                    time.sleep(polling_interval)
                    continue
            return price0CumulativeLast, price1CumulativeLast, blockTimestampLast
        
    def calculate_twap(
        self,
        currentPrice: int,
        prevPrice: int,
        blockTimestampLast: int,
        prevBlockTimestampLast: int,
        tokenIdx: str
    ) -> float:
        sub = (currentPrice - prevPrice) / 2**112
        logger.info(
            f"""
            Calculated the following TWAP price ({tokenIdx}):"
            ({sub}) / ({blockTimestampLast} - {prevBlockTimestampLast})
            """
        )
        return (sub) / (blockTimestampLast - prevBlockTimestampLast)
    
    def _get_total_value_locked(self):
        reserve0, reserve1, _ = self._callGetReserves()
        vl0 = ((1e18 * reserve1) / (reserve0 + 1e18)) * reserve0 # value locked token0 without fees
        vl1 = ((1e18 * reserve0) / (reserve1 + 1e18)) * reserve1 # value locked token0 without fees
        tvl = vl0 + vl1 # total value locked of the pool
        return tvl

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface"""

        asset = asset.lower()
        currency = currency.lower()

        if currency not in  ["usdc", "dai", "usdt"]:
            logger.error(f"Currency not supported: {currency}")
            return None, None

        self._initialize_lp_contract(currency)

        try:
            prevPrice0CumulativeLast, prevPrice1CumulativeLast, prevBlockTimestampLast = self.get_prev_prices_cumulative()

            price0CumulativeLast, price1CumulativeLast, blockTimestampLast = self.poll_to_get_currentPrices(
                prevPrice0CumulativeLast,
                prevPrice1CumulativeLast,
                prevBlockTimestampLast
            )

            twap = self.calculate_twap(
                price0CumulativeLast, prevPrice0CumulativeLast, blockTimestampLast, prevBlockTimestampLast, "token0"
            )

            try:
                token0, _ = self.lps_order[currency].split('/')
                if "pls" not in token0.strip(): twap = self.calculate_twap(
                    price1CumulativeLast, prevPrice1CumulativeLast, blockTimestampLast, prevBlockTimestampLast, "token1"
                )
            except KeyError as e:
                logger.error(f'currency {currency} not found in the provided PLS_CURRENCY_SOURCES')
                logger.error(e)

            self._write_prices_as_json(
                price0CumulativeLast,
                price1CumulativeLast,
                blockTimestampLast,
                "Cumulative prices JSON data updated"
            )

            price = float(twap / 1e18)
            if currency == 'usdc' or currency == 'usdt':
                price = price * 1e12

            logger.info(f"""
            TWAP LP price for {asset}-{currency}: {price}
            LP contract address: {self.contract_addresses[currency]}
            """)

            weight = self._get_total_value_locked()

            return price, datetime_now_utc(), float(weight)
        except Exception as e:
            logger.error(e)
            return None, None

@dataclass
class TWAPLPSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: TWAPLPSpotPriceService = field(default_factory=TWAPLPSpotPriceService, init=False)
