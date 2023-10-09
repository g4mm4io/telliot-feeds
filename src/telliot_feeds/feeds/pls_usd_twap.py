"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.twap import TWAPSpotPriceSource
from dotenv import load_dotenv
from telliot_feeds.utils.log import get_logger

load_dotenv()
logger = get_logger(__name__)

pls_usd_twap_feed = DataFeed(
    query=SpotPrice(
        asset="pls",
        currency="usd"
     ),
    source=TWAPSpotPriceSource(
        asset="pls",
        currency="usd"
    ),
)