import os
from decimal import *
from collections import defaultdict
from datetime import datetime

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from eth_utils.conversions import to_bytes
from eth_abi import decode_abi

import requests

from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.pricing.price_service import WebPriceService
from telliot_feeds.pricing.price_source import PriceSource
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)

class TWAPSpotPriceService(WebPriceService):
    """TWAP Price Service"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs["name"] = "TWAP Price Service"
        kwargs["url"] = os.getenv("FETCH_FLEX_SUBGRAPH_URL")

        self.timespan = int(os.getenv("TWAP_TIMESPAN", 3600))
        self.twap: dict[str, dict[Decimal, int]] = defaultdict(lambda: {'total': Decimal('0.0'), 'count': 0})

        super().__init__(**kwargs)
    
    def _bytes_from_string(self, string: str) -> bytes: return to_bytes(hexstr=string)

    def _decode_query_data(self, query_data: str) -> tuple[str, str]:
        query_type, encoded_param_values = decode_abi(["string", "bytes"], bytes(query_data))
        param_values = decode_abi(['string', 'string'], encoded_param_values)
        return param_values

    def _get_current_timestamp(self) -> int:
        now = datetime.now()
        return int(now.timestamp())
    
    def _get_last_reports_gte_timestamp(self, timestamp: int) -> list[dict]:
        query_body = f"""
            query newReportEntities {{
                newReportEntities(where: {{_time_gte: {timestamp} }}) {{
                    _nonce
                    _queryData
                    _queryId
                    _reporter
                    _time
                    _value
                    txnHash
                    id
                }}
            }}
        """
        response = requests.post(url=self.url, json={"query": query_body})

        if response.status_code != 200 or response.json().get('errors'):
            err_msg = f"""
            Failed to query subgraph {self.url}, status code: {response.status_code}
            Error:
            {response.json()}
            """
            logger.error(err_msg)
            raise Exception(err_msg)
        
        return response.json()['data']['newReportEntities']
    
    def _get_TWAP_from_reports(self) -> dict[str, float]:
        timestamp = self._get_current_timestamp() - self.timespan
        reports = self._get_last_reports_gte_timestamp(timestamp)
        for report in reports:
            asset, currency = self._decode_query_data(self._bytes_from_string(string=report['_queryData']))
            decoded_value, = decode_abi(['uint256',], self._bytes_from_string(report['_value']))
            decimal_value = Decimal(f'{(decoded_value / 1e18):.18f}')
        
            key = f'{asset}-{currency}'
            self.twap[key]['total'] += decimal_value
            self.twap[key]['count'] += 1

        means: dict[str, float] = {}
        for key in self.twap.keys():
            total, count = self.twap[key]['total'], self.twap[key]['count']
            mean = (total / count).quantize(Decimal('1e-18'))
            means[key] = float(mean)
        return means

    async def get_price(self, asset: str, currency: str) -> OptionalDataPoint[float]:
        """Implement PriceServiceInterface"""

        asset = asset.lower()
        currency = currency.lower()

        try:
            twap_from_reports = self._get_TWAP_from_reports()
            price = twap_from_reports[f'{asset}-{currency}']
            logger.info(f"""
            TWAP price found for {asset}-{currency} in the last {self.timespan} seconds: {price}
            """)
            return price, datetime_now_utc()
        except KeyError as e:
            logger.error(f"""
            No TWAP price found for {asset}-{currency}
            TWAP must have at least 1 report in the last {self.timespan} seconds.
            """)
            logger.error(e)
            return None, None
        except Exception as e:
            logger.error(e)
            return None, None

@dataclass
class TWAPSpotPriceSource(PriceSource):
    asset: str = ""
    currency: str = ""
    service: TWAPSpotPriceService = field(default_factory=TWAPSpotPriceService, init=False)
