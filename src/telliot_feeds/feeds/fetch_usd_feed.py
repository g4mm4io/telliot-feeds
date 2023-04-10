"""Datafeed for current price of FETCH in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

fetch_usd_median_feed = DataFeed(
    query=SpotPrice(asset="fetch", currency="usd"),
    source=PriceAggregator(
        asset="fetch",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="fetch", currency="usd"),
            CoinbaseSpotPriceSource(asset="fetch", currency="usd"),
        ],
    ),
)
