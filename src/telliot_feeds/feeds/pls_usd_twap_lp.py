from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.twap_lp import TWAPLPSpotPriceSource
from dotenv import load_dotenv
from telliot_feeds.utils.log import get_logger
import os

load_dotenv()
logger = get_logger(__name__)

currency = os.getenv("PLS_CURRENCY_SOURCES").split(',')[0]

pls_usd_twap_lp_feed = DataFeed(
    query=SpotPrice(
        asset="pls",
        currency="usd"
     ),
    source=TWAPLPSpotPriceSource(
        asset="pls",
        currency=currency
    )
)