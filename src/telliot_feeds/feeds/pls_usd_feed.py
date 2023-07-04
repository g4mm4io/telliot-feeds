"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.pulsechain_pulsex import PulsechainPulseXSource
from dotenv import load_dotenv
from telliot_feeds.utils.log import get_logger
import os

load_dotenv()
logger = get_logger(__name__)

sources = os.getenv("PLS_CURRENCY_SOURCES")

if os.getenv("PLS_CURRENCY_SOURCES"):
    sources_list = sources.split(',')
    sources_objs = []
    for s in sources_list:
        sources_objs.append(PulsechainPulseXSource(asset="pls", currency=s))

    pls_usd_feed = DataFeed(
        query=SpotPrice(asset="pls", currency="usd"),
        source=PriceAggregator(
            asset="pls",
            currency="usd",
            algorithm="weighted_average",
            sources=sources_objs,
        ),
    )
elif os.getenv("COINGECKO_MOCK_URL"):
    pls_usd_feed = DataFeed(
        query=SpotPrice(asset="pls", currency="usd"), source=CoinGeckoSpotPriceSource(asset="pulsechain", currency="usd")
    )
else:
    pls_usd_feed = DataFeed(
         query=SpotPrice(asset="pls", currency="usd"), source=PulsechainSubgraphSource(asset="pls", currency="usd")
    )
