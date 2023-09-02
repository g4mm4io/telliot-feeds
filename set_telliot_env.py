import os
import argparse
import pathlib

parser = argparse.ArgumentParser(
    description="""
    Set Telliot environment variables.
    If this script is not executed or there is no telliot-core/.env file,
    the default environment is used.
    """
)
parser.add_argument(
    '-e',
    '--env',
    type=str,
    choices=['default', 'dev', 'testnet', 'mainnet', 'preprod', 'staging'],
    help='Telliot environment to use, choices = %(choices)s',
    required=True
)
args = parser.parse_args()

telliot_core_env_path = pathlib.Path(__file__).absolute().resolve().parents[1] / 'telliot-core' / '.env'

with open(telliot_core_env_path, 'w') as file:
    file.write(f'ENV_NAME={args.env}\n')

print(f'Telliot environment set to {args.env}')