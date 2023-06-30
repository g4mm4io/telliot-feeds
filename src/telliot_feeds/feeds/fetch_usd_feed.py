"""Datafeed for current price of FETCH in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource

fetch_usd_median_feed = DataFeed(
    query=SpotPrice(asset="fetch", currency="usd"),
    source=CoinGeckoSpotPriceSource(asset="fetch", currency="usd")
)
