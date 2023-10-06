"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.twap import TWAP
from telliot_feeds.sources.manual.twap_manual_input_source import TWAPManualSource
from dotenv import load_dotenv
from telliot_feeds.utils.log import get_logger
import os

load_dotenv()
logger = get_logger(__name__)

sources = os.getenv("PLS_CURRENCY_SOURCES")

timespan = int(os.getenv("TWAP_TIMESPAN"))

pls_usd_twap_feed = DataFeed(
    query=TWAP(
        asset="pls",
        currency="usd",
        timespan=timespan,
    ),
    source=TWAPManualSource(),
)