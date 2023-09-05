import statistics

import pytest

from telliot_feeds.feeds.fetch_usd_feed import fetch_usd_median_feed


@pytest.mark.skip()
@pytest.mark.asyncio
async def test_fetch_asset_price_feed():
    """Retrieve median FETCH/USD price."""
    v, _ = await fetch_usd_median_feed.source.fetch_new_datapoint()

    assert v is not None
    assert v > 0
    print(f"FETCH/USD Price: {v}")

    # Get list of data sources from sources dict
    source_prices = [source.latest[0] for source in fetch_usd_median_feed.source.sources]

    # Make sure error is less than decimal tolerance
    assert (v - statistics.median(source_prices)) < 10**-6
