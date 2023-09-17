cd ../telliot-core

python3 change_address.py
cat ./src/telliot_core/data/contract_directory.json

telliot config init

sleep 30 #Allow some time to pull the secret private key

directory_path="/mnt/secrets-store"
directory_path_contents=$(cat "$directory_path")
export PRIVATE_KEY="$directory_path_contents"

echo -e "$ACC_PWD\n$ACC_PWD\n" | telliot account add myacct$ACC_NUMBER $PRIVATE_KEY $NETWORK_ID
echo "Account myacct$ACC_NUMBER created!"

echo -e "yes\n$ACC_PWD\n" | telliot report -a myacct$ACC_NUMBER -qt $QUERY_TAG -s $STAKE_AMOUNT -ncr --fetch-flex -wp 900