"""Example datafeed used by PLSUSDReporter."""
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.pulsechain_subgraph import PulsechainSubgraphSource
from telliot_feeds.sources.price.spot.pulsechain_secoracle import PulsechainSecOracleSource

pls_usd_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainSubgraphSource(asset="pls", currency="usd")
)

pls_usdc_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainSecOracleSource(asset="pls", currency="usdc")
)

pls_dai_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainSecOracleSource(asset="pls", currency="dai")
)

pls_plsx_feed = DataFeed(
    query=SpotPrice(asset="pls", currency="usd"), source=PulsechainSecOracleSource(asset="pls", currency="plsx")
)
