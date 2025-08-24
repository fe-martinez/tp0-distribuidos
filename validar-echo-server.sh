#!/bin/bash

TEST_MESSAGE="Hello, Echo Server!"
SERVER_CONTAINER_NAME="server"
TEMP_CONTAINER_NAME="temp-nc-container"
NETWORK_NAME="tp0_testing_net"
SERVER_PORT=12345

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "error: Docker network '$NETWORK_NAME' does not exist."
  exit 1
fi

docker run --rm \
    --name $TEMP_CONTAINER_NAME \
    --network $NETWORK_NAME \
    busybox sh -c "echo '$TEST_MESSAGE' | nc $SERVER_CONTAINER_NAME $SERVER_PORT | grep -q '$TEST_MESSAGE'"

if [ $? -eq 0 ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
