import os
import argparse
import pathlib

parser = argparse.ArgumentParser(
    description="""
    Set Telliot environment variables.
    If this script is not executed or there is no telliot-core/.env file,
    the default environment is used.
    """,
    formatter_class=argparse.RawTextHelpFormatter
)
parser.add_argument(
    '-e',
    '--env',
    type=str,
    choices=['default', 'testnet', 'mainnet'],
    help='''
    Telliot environment to use, choices = %(choices)s

    The 'default' env will configure telliot-core to use contract_directory.json
    instead of contract_directory.<ENV_NAME>.json.
    ''',
    required=True
)
args = parser.parse_args()

telliot_core_env_path = pathlib.Path(__file__).absolute().resolve().parents[1] / 'telliot-core'

if not telliot_core_env_path.exists():
    telliot_core_env_path = pathlib.Path(__file__).absolute().resolve().parents[0] / 'telliot-core'

if not telliot_core_env_path.exists():
    raise FileNotFoundError("telliot-core directory not found in parent directory nor in current directory")

telliot_core_env_path = telliot_core_env_path / '.env'

lines = []
if telliot_core_env_path.exists():
    # if .env file exists, read it to keep all configurations and overwrite ENV_NAME
    with open(telliot_core_env_path, 'r') as file:
        lines = file.readlines()
        lines = [line for line in lines if not line.startswith('ENV_NAME')]
        lines = [line if line.endswith('\n') else line + '\n' for line in lines]

lines += [f'ENV_NAME={args.env}\n']

with open(telliot_core_env_path, 'w') as file:
    file.write("".join(lines))

print(f'Telliot environment set to {args.env}')