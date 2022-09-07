from asyncio.log import logger
import os
from typing import Optional

from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig


def mainnet_config() -> Optional[TelliotConfig]:
    cfg = TelliotConfig()
    cfg.main.chain_id = 1
    endpoint = cfg.get_endpoint()

    if "INFURA_API_KEY" in endpoint.url:
        endpoint.url = f'wss://mainnet.infura.io/ws/v3/{os.environ["INFURA_API_KEY"]}'

    accounts = find_accounts(chain_id=1)
    if not accounts:
        # Create a test account using PRIVATE_KEY defined on github.
        key = os.getenv("PRIVATE_KEY", None)
        if key:
            ChainedAccount.add("git-mainnet-key", chains=1, key=os.environ["PRIVATE_KEY"], password="")
        else:
            logger.warning("No mainnet account added!")
            return None

    return cfg
