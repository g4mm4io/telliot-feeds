from dataclasses import dataclass
from dataclasses import field
from typing import Any

from dotenv import load_dotenv

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger

from web3 import Web3
import os

load_dotenv()

addrs = {}
if os.getenv("PLS_CURRENCY_SOURCES") and os.getenv("PLS_ADDR_SOURCES"):
    sources_addrs = "0x38c4bB88FCAf4Ba045ec34C8a2C290Ff74c2b79f"
    sources = "dai"
    sources_list = sources.split(',')
    sources_addr_list = sources_addrs.split(',')

    for i, s in enumerate(sources_list):
        addrs[s] = Web3.toChecksumAddress(sources_addr_list[i])

logger = get_logger(__name__)


def get_amount_out(amount_in, reserve_in, reserve_out):
    """
    Given an input asset amount, returns the maximum output amount of the
    other asset (accounting for fees) given reserves.

    :param amount_in: Amount of input asset.
    :param reserve_in: Reserve of input asset in the pair contract.
    :param reserve_out: Reserve of input asset in the pair contract.
    :return: Maximum amount of output asset.
    """
    assert amount_in > 0
    assert reserve_in > 0 and reserve_out > 0
    amount_in_with_fee = amount_in*997
    numerator = amount_in_with_fee*reserve_out
    denominator = reserve_in*1000 + amount_in_with_fee
    return int(numerator/denominator)


class PulseX_PLSXDAI_Service(WebPriceService):
    """Pulsechain PulseX Price Service for PLS/USD feed"""

    logger.warning(f"inside PulseX_PLSXDAI_Service")

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "Earn Protocol PulseX Price Service"
        kwargs["url"] = "https://rpc.v4.testnet.pulsechain.com"
        kwargs["timeout"] = 10.0
        super().__init__(**kwargs)

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface
        This implementation gets the price from the Pulsechain PulseX Service
        """

        asset = asset.lower()
        currency = currency.lower()

        if currency not in ["usdc", "dai"]:
            logger.error(f"Currency not supported: {currency}")
            return None, None

        # contract_addr = addrs.get(currency)
        contract_addr = "0x38c4bB88FCAf4Ba045ec34C8a2C290Ff74c2b79f"

        if asset != 'plsx':
            logger.error(f"Asset not supported: {asset}")
            return None, None

        getReservesAbi = '[{"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"reserve0","type":"uint112"},{"internalType":"uint112","name":"reserve1","type":"uint112"},{"internalType":"uint32","name":"blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"}]'
        w3 = Web3(Web3.HTTPProvider(
            self.url, request_kwargs={'timeout': self.timeout}))
        try:
            contract = w3.eth.contract(
                address=contract_addr, abi=getReservesAbi)
            [reserve0, reserve1, timestamp] = contract.functions.getReserves().call()
            # val = get_amount_out(1e18, reserve1, reserve0)
            val = (reserve0/reserve1)

            vl0 = ((1e18 * reserve1) / (reserve0 + 1e18)) * \
                reserve0  # value locked token0 without fees
            vl1 = ((1e18 * reserve0) / (reserve1 + 1e18)) * \
                reserve1  # value locked token0 without fees
            tvl = vl0 + vl1  # total value locked of the pool

        except Exception as e:
            logger.warning(
                f"No prices retrieved from Pulsechain Sec Oracle with Exception {e}")
            return None, None

        try:
            price = float(val)
            if currency == 'usdc':
                price = price * 1e12  # scale usdc
            return price, timestamp, float(tvl)
        except Exception as e:
            msg = f"Error parsing Pulsechain Sec Oracle response: KeyError: {e}"
            logger.critical(msg)
            return None, None


@dataclass
class PulseX_PLSXDAI_Source(PriceSource):
    asset: str = ""
    currency: str = ""
    addr: str = ""
    service: PulseX_PLSXDAI_Service = field(
        default_factory=PulseX_PLSXDAI_Service, init=False)
