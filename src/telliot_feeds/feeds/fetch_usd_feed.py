"""Datafeed for current price of FETCH in USD."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.pulsex_subgraph import PulseXSupgraphSource
from dotenv import load_dotenv
import os

load_dotenv()

if os.getenv("PULSEX_SUBGRAPH_URL"):
    fetch_usd_median_feed = DataFeed(
        query=SpotPrice(asset="fetch", currency="usd"),
        source=PulseXSupgraphSource(asset="fetch", currency="usd")
    )
else:
    fetch_usd_median_feed = DataFeed(
        query=SpotPrice(asset="fetch", currency="usd"),
        source=CoinGeckoSpotPriceSource(asset="fetch", currency="usd")
    )