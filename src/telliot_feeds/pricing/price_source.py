from dataclasses import dataclass
from dataclasses import field

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import OptionalWeightedDataPoint
from telliot_feeds.pricing.price_service import WebPriceService


@dataclass
class PriceSource(DataSource[float]):
    """Current Asset Price

    The Current Asset Price data source retrieves the price of a asset
    in the specified current from a `WebPriceService`.
    """

    #: Asset symbol
    asset: str = ""

    #: Price currency symbol
    currency: str = ""

    #: Price Service
    service: WebPriceService = field(default_factory=WebPriceService)  # type: ignore

    async def fetch_new_datapoint(self) -> OptionalWeightedDataPoint[float]:
        """Update current value with time-stamped value fetched from source

        Returns:
            New datapoint
        """
        datapoint = await self.service.get_price(self.asset, self.currency)
        v = datapoint[0]
        t = datapoint[1]
        if v is not None and t is not None:
            self.store_datapoint((v, t))

        return datapoint
