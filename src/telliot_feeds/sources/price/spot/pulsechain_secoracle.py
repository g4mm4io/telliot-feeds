from dataclasses import dataclass
from dataclasses import field
from typing import Any

import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

from web3 import Web3

logger = get_logger(__name__)
pulsechain_secondary_oracles = {
    "plsx": "0x5a3d5c3F0C10cab165D1A2279915BCa91F75D345",
    "dai": "0x9f838cE132684758B9628D3212E1b8a5914C49ce",
    "usdc": "0xAb9E8788b4b8aBf795f6fe4B4e80688A5e36ED5E"
}


class PulsechainSecOracleService(WebPriceService):
    """Pulsechain Secondary Orcale Price Service for PLS/USD feed"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "LiquidLoans Secondary Oracle Price Service"
        kwargs["url"] = "https://rpc.v4.testnet.pulsechain.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface

        This implementation gets the price from the Pulsechain Secondary Oracle Service

        """

        asset = asset.lower()
        currency = currency.lower()

        if currency not in ["usdc", "dai", "plsx"]:
            logger.error(f"Currency not supported: {currency}")
            return None, None

        contract_addr = pulsechain_secondary_oracles.get(currency)
        
        if asset != 'pls':
            logger.error(f"Asset not supported: {asset}")
            return None, None

        abi = '[{"inputs":[],"name":"getPrice","outputs":[{"internalType":"bool","name":"","type":"bool"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"}]'

        w3 = Web3(Web3.HTTPProvider(self.url, request_kwargs={'timeout': self.timeout}))
        try:
            contract = w3.eth.contract(address=contract_addr, abi=abi)
            [_, val, timestamp, _] = contract.functions.getPrice().call()

        except Exception as e:
            logger.warning(f"No prices retrieved from Pulsechain Sec Oracle with Exception {e}")
            return None, None

        try:
            price = float(val)
            return price, timestamp
        except Exception as e:
            msg = f"Error parsing Pulsechain Sec Oracle response: KeyError: {e}"
            logger.critical(msg)
            return None, None


@dataclass
class PulsechainSecOracleSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: PulsechainSecOracleService = field(default_factory=PulsechainSecOracleService, init=False)
