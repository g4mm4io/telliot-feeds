cd ../telliot-core

python3 change_address.py
cat ./src/telliot_core/data/contract_directory.json

telliot config init

sleep 60 #Allow some time to pull the secret private key

directory_path="/mnt/secrets-store"

# Check if the directory exists
if [ -d "$directory_path" ]; then
    # Get the count of files in the directory
    file_count=$(find "$directory_path" -maxdepth 1 -type f | wc -l)

    # Check if there's only one file in the directory
    if [ "$file_count" -eq 1 ]; then
        # Get the path of the only file in the directory
        file_path=$(find "$directory_path" -maxdepth 1 -type f)

        # Read the content of the file into a variable
        file_content=$(cat "$file_path")

        # Set the content as an environment variable
        export PRIVATE_KEY="$file_content"

        echo "Environment variable set with content from the file."
    elif [ "$file_count" -eq 0 ]; then
        echo "No files found in the directory."
    else
        echo "Multiple files found in the directory. Unable to determine which file to use."
    fi
else
    echo "Directory not found."
fi

echo -e "$ACC_PWD\n$ACC_PWD\n" | telliot account add myacct$ACC_NUMBER $PRIVATE_KEY $NETWORK_ID
echo "Account myacct$ACC_NUMBER created!"

echo -e "yes\n$ACC_PWD\n" | telliot report -a myacct$ACC_NUMBER -qt $QUERY_TAG -s $STAKE_AMOUNT -ncr --fetch-flex -wp 900