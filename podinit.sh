cd ../telliot-core

python3 change_address.py
cat ./src/telliot_core/data/contract_directory.json

telliot config init

pk_path="/mnt/secrets-store/${SECRET_NAME}"
telliot_pw_path="/mnt/telliot-password/${TELLIOT_PASSWORD}"
pk_path_contents=$(cat "$pk_path") > /dev/null 2>&1
telliot_pw_path_contents=$(cat "$telliot_pw_path") > /dev/null 2>&1
export PRIVATE_KEY="$pk_path_contents" > /dev/null 2>&1
export ACC_PWD="$telliot_pw_path_contents" > /dev/null 2>&1

echo -e "$ACC_PWD\n$ACC_PWD\n" | telliot account add myacct$ACC_NUMBER $PRIVATE_KEY $NETWORK_ID > /dev/null 2>&1
echo "Account myacct$ACC_NUMBER created!"

echo -e "yes\n$ACC_PWD\n" | telliot report -a myacct$ACC_NUMBER -qt $QUERY_TAG -s $STAKE_AMOUNT -ncr --fetch-flex -wp $WAIT_PERIOD > /dev/null 2>&1