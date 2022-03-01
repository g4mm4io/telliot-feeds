import pytest
from telliot_core.api import DataFeed
from telliot_core.apps.core import TelliotCore
from telliot_core.queries.diva_protocol import divaProtocolPolygon

from telliot_feed_examples.feeds.diva_protocol_feed import assemble_diva_datafeed
from telliot_feed_examples.sources.price.historical.poloniex import (
    PoloniexHistoricalPriceSource,
)


@pytest.mark.asyncio
async def test_diva_datafeed(ropsten_cfg) -> None:
    async with TelliotCore(config=ropsten_cfg) as core:
        account = core.get_account()
        feed = await assemble_diva_datafeed(
            pool_id=159, node=core.endpoint, account=account
        )

        assert isinstance(feed, DataFeed)
        assert isinstance(feed.query, divaProtocolPolygon)
        assert isinstance(feed.source.sources[3], PoloniexHistoricalPriceSource)
        assert isinstance(feed.source.sources[0].ts, int)
        assert feed.source.asset == "btc"
        assert feed.source.sources[2].currency == "dai"

        # v, t = await feed.source.fetch_new_datapoint()
        # assert v > 25000
        # assert t == 123412341234
