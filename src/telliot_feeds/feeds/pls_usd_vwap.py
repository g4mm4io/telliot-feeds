from telliot_feeds.datafeed import DataFeed
from telliot_feeds.sources.price_aggregator import PriceAggregator
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.twap_lp import TWAPLPSpotPriceSource
from dotenv import load_dotenv
from telliot_feeds.utils.log import get_logger
import os

load_dotenv()
logger = get_logger(__name__)

def get_sources_objs():
    sources = os.getenv("PLS_CURRENCY_SOURCES")
    sources_list = sources.split(',')
    sources_objs = []
    for s in sources_list:
        sources_objs.append(TWAPLPSpotPriceSource(asset="pls", currency=s))
    return sources_objs

pls_usd_vwap_feed = DataFeed(
    query=SpotPrice(
        asset="pls",
        currency="usd"
     ),
    source=PriceAggregator(
            asset="pls",
            currency="usd",
            algorithm="weighted_average",
            sources=get_sources_objs(),
    )
)