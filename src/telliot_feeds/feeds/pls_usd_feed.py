"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsechain_subgraph import PulsechainSubgraphSource
from telliot_feeds.sources.price.spot.pulsechain_pulsex import PulsechainPulseXSource
from dotenv import load_dotenv
from telliot_feeds.utils.log import get_logger
import os

load_dotenv()
logger = get_logger(__name__)

PLS_SOURCE = os.getenv("PLS_SOURCE")

pls_usd_graphql_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainSubgraphSource(asset="pls", currency="usd")
)

pls_usdc_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainPulseXSource(asset="pls", currency="usdc")
)

pls_dai_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainPulseXSource(asset="pls", currency="dai")
)

pls_plsx_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainPulseXSource(asset="pls", currency="plsx")
)

pls_sources = {
    'dai': pls_dai_feed,
    'usdc': pls_usdc_feed,
    'plsx': pls_plsx_feed,
    'graphql': pls_usd_graphql_feed
}

if PLS_SOURCE in pls_sources.keys():
    logger.info(PLS_SOURCE + ' selected')
    pls_usd_feed = pls_sources.get(PLS_SOURCE)
else:
    logger.info('GraphQL selected')
    pls_usd_feed = pls_usd_graphql_feed

