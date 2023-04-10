from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.fetch_rng import FetchRNG
from telliot_feeds.sources.manual.fetch_rng_manual_source import FetchRNGManualInputSource


timestamp = None

fetch_rng_manual_feed = DataFeed(
    query=FetchRNG(timestamp=timestamp), source=FetchRNGManualInputSource()  # type: ignore
)
