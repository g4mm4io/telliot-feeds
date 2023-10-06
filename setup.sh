
#!/bin/bash

python3.9 -m venv tenv
source tenv/bin/activate

cd ../telliot-core

echo "Installing dependencies for telliot core"
pip install -e .
pip install -r requirements-dev.txt

cd ../telliot-feeds

echo "Installing dependencies for telliot feed"
pip install -e .
pip install -r requirements.txt
