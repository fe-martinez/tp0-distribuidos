#!/bin/bash

OUTPUT_FILE=$1
CLIENT_COUNT=$2

echo "Generating Docker Compose file: $OUTPUT_FILE"
echo "Client count: $CLIENT_COUNT"

cat > $OUTPUT_FILE <<EOL
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 ./main.py
    environment:
        - PYTHONUNBUFFERED=1
        - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
EOL

for i in $(seq 1 $CLIENT_COUNT); do
  cat >> $OUTPUT_FILE << EOL

  client${i}:
    container_name: client${i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=${i}
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server
EOL
done

cat >> $OUTPUT_FILE << EOL

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOL

echo "Successfully created ${OUTPUT_FILE}."