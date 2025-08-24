#!/bin/bash

TEST_MESSAGE="Hello, Echo Server!"
SERVER_CONTAINER_NAME="server"
TEMP_CONTAINER_NAME="temp-nc-container"
NETWORK_NAME="tp0_testing_net"
SERVER_PORT=12345
TIMEOUT=5

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
  echo "action: test_echo_server | result: fail"
  exit 0
fi

TEST_OUTPUT=$(docker run --rm \
    --name $TEMP_CONTAINER_NAME \
    --network $NETWORK_NAME \
    busybox sh -c "echo '$TEST_MESSAGE' | timeout $TIMEOUT nc $SERVER_CONTAINER_NAME $SERVER_PORT" 2>&1)

DOCKER_EXIT=$?
if [ $DOCKER_EXIT -ne 0 ]; then
  echo "action: test_echo_server | result: fail"
  exit 0
fi

if [ "$TEST_OUTPUT" = "$TEST_MESSAGE" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
