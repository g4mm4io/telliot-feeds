import os
import signal
import sys
import logging
import pexpect
import subprocess
import argparse
from argparse import RawTextHelpFormatter
from pathlib import Path
from decimal import *
from web3 import Web3
from telliot_core.directory import contract_directory

MOCK_PRICE_API_PORT=3001

logger = logging.getLogger('telliot_e2e_tests')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s | %(name)s | %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

class Contract:
    def __init__(self, oracle_address: str, provider_url: str = "https://rpc.v4.testnet.pulsechain.com"):
        # TODO parameterize these
        self.oracle_address = oracle_address
        self.provider_url = provider_url
        self.oracle = None

    def initialize(self):
        try:
            w3 = Web3(Web3.HTTPProvider(self.provider_url))

            abi = """
            [
            {
                "inputs": [
                {
                    "internalType": "bytes32",
                    "name": "_queryId",
                    "type": "bytes32"
                }
                ],
                "name": "getCurrentValue",
                "outputs": [
                {
                    "internalType": "bytes",
                    "name": "_value",
                    "type": "bytes"
                }
                ],
                "stateMutability": "view",
                "type": "function"
            }
            ]
            """
            self.oracle = w3.eth.contract(address=self.oracle_address, abi=abi)
            logger.info(f'Oracle contract at address {self.oracle_address} initialized')
        except Exception as e:
            logger.error("Oracle contract initialization error:")
            logger.error(e)

    @staticmethod
    def create(oracle_address: str, provider_url: str):
        instance = Contract(oracle_address, provider_url)
        instance.initialize()
        return instance

    def _bytes_to_decimal(self, bytes: bytes) -> Decimal:
        decoded_value = int.from_bytes(bytes, byteorder='big')
        formatted_value = f'{(decoded_value / 1e18):.18f}'
        return Decimal(formatted_value)

    def get_current_value_as_decimal(self, queryId: str):
        current_value: bytes = self.oracle.functions.getCurrentValue(
            queryId).call()
        return self._bytes_to_decimal(current_value)

def _get_new_price(price: Decimal) -> Decimal:
    return (price * Decimal('1.2')).quantize(Decimal('1e-18'))

def _configure_mock_price_api_env(mock_price_path: Path, new_price: Decimal) -> None:
    env_file = mock_price_path / '.env'

    lines = []
    if env_file.exists():
        with open(env_file, 'r') as file:
            lines = file.readlines()
            lines = [line for line in lines if not line.startswith('SERVER_PORT') or not line.startswith('PLS_PRICE')]
            lines = [line if line.endswith('\n') else line + '\n' for line in lines]
    lines += [f'SERVER_PORT={MOCK_PRICE_API_PORT}\n', f'PLS_PRICE={new_price}\n']
    with open(env_file, 'w') as file:
        file.write("".join(lines))

def initialize_mock_price_api(price: Decimal) -> subprocess.Popen:
    current_dir = Path(__file__).parent.absolute()
    mock_price_path = current_dir.parent.absolute() / 'mock-price-api'

    _configure_mock_price_api_env(mock_price_path, price)

    os.chdir(mock_price_path)
    process = subprocess.Popen(['npm', 'start'], preexec_fn=os.setsid)
    os.chdir(current_dir)

    logger.info(f"MOCK_PRICE_API initialized with price {price}")
    return process

def _configure_telliot_env(env_config: list[str] = None) -> list[str]:
    current_dir = Path(__file__).parent.absolute()
    telliot_path = current_dir.parent.absolute() / 'telliot-feeds'
    env_file = telliot_path / '.env'

    if env_config != None:
        with open(env_file, 'w') as file:
            file.write("".join(env_config))
        logger.info(f"TELLIOT original env configuration restored")
        return []

    prev_env_config = []
    env_file = telliot_path / '.env'
    if env_file.exists():
        with open(env_file, 'r') as file:
            prev_env_config = file.readlines()
            prev_env_config = [line if line.endswith('\n') else line + '\n' for line in prev_env_config]
        logger.info("TELLIOT original env configuration saved")
    with open(env_file, 'w') as file:
        file.write(f"COINGECKO_MOCK_URL=http://localhost:{MOCK_PRICE_API_PORT}/coingecko")
    logger.info(f"TELLIOT env configuration updated")
    return prev_env_config

def submit_report_with_telliot(account_name: str, stake_amount: str) -> None:
    prev_env_config = _configure_telliot_env()

    try:
        report = f'telliot report -a {account_name} -ncr -qt pls-usd-spot --fetch-flex --submit-once -s {stake_amount}'
        logger.info(f"Submitting report: {report}")
        report_process = pexpect.spawn(report, timeout=None)
        report_process.logfile = sys.stdout.buffer
        report_process.expect("\w+\r\n")
        report_process.sendline('y')
        report_process.expect("\w+\r\n")
        report_process.sendline('')
        report_process.expect("\w+\r\n")
        report_process.sendline('')
        report_process.expect("\w+\r\n")
        report_process.sendline('')
        report_process.expect(pexpect.EOF)
        report_process.close()
        logger.info("Submit report with telliot OK")
    except Exception as e:
        logger.error("Submit report with telliot error:")
        logger.error(e)
    finally:
        _configure_telliot_env(prev_env_config)

def main():
    parser = argparse.ArgumentParser(
        description="Telliot submit price E2E test",
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        '-a',
        '--account',
        type=str,
        required=True,
        help=('Account name to be used in the telliot 2e2 test.\n'
        'You can get accounts by running the following command\n'
        '"telliot account find"')
    )
    parser.add_argument(
        '-s',
        '--stake',
        type=str,
        required=True,
        help=('Stake amount to submit a report.\n'
        'The minimum stake amount depends on the the FetchFlex deployment\n'
        'Please refer monorepo/fetch-contracts and fetchFlex.sol contract')
    )
    parser.add_argument(
        '-chain',
        '--chain-id',
        type=int,
        choices=[943, 369],
        required=True,
        help=('Telliot environment to use, choices = %(choices)s\n'
        'The "default" env will configure telliot-core to use contract_directory.json\n'
        'instead of contract_directory.<ENV_NAME>.json.'),
        default='943'
    )
    parser.add_argument(
        '-p',
        '--provider-url',
        type=str,
        required=False,
        help=('Provider url to use for the Oracle contract.\n'
        'Default is https://rpc.v4.testnet.pulsechain.com'),
        default='https://rpc.v4.testnet.pulsechain.com'
    )

    args = parser.parse_args()

    account_name = args.account
    stake_amount = args.stake
    chain_id = args.chain_id
    provider_url = args.provider_url

    contract = contract_directory.find(chain_id=chain_id, name="fetchflex-oracle")[0]
    oracle_address = contract.address[chain_id]

    logger.info(f"""
        Starting E2E test for telliot submit price, config:
        account name: {account_name}
        stake amount: {stake_amount}
        chain id: {chain_id}
        provider url: {provider_url}
        oracle address: {oracle_address}
    """)

    contract = Contract.create(
        oracle_address=oracle_address,
        provider_url=provider_url
    )
    queryId = "0x83245f6a6a2f6458558a706270fbcc35ac3a81917602c1313d3bfa998dcc2d4b"

    price: Decimal = contract.get_current_value_as_decimal(queryId)
    logger.info(f"Price for {queryId} is {price} USD")

    new_price: Decimal = _get_new_price(price)
    mock_price_ps = initialize_mock_price_api(new_price)

    submit_report_with_telliot(account_name=account_name, stake_amount=stake_amount)

    price: Decimal = contract.get_current_value_as_decimal(queryId)
    logger.info(f"Price after report for {queryId} is {price} USD")
    try:
        assert abs(price - new_price) <= Decimal('1e-15')
        logger.info('OK - Submit price test passed (considering 15 decimals)')
    except AssertionError as e:
        logger.error('FAIL - Submit price test failed')
        logger.error(e)
    finally:
        os.killpg(os.getpgid(mock_price_ps.pid), signal.SIGTERM)

if __name__ == "__main__":
    main()
