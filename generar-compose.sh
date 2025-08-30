#!/bin/bash

# Script to generate Docker Compose file for tp0
# Usage: ./generar-compose.sh [OUTPUT_FILE] [CLIENT_COUNT]
# Example: ./generar-compose.sh docker-compose.yaml 3

DEFAULT_OUTPUT_FILE="docker-compose.yaml"
DEFAULT_CLIENT_COUNT=1

OUTPUT_FILE=${1:-$DEFAULT_OUTPUT_FILE}
CLIENT_COUNT=${2:-$DEFAULT_CLIENT_COUNT}

if [[ ! "$CLIENT_COUNT" =~ ^[0-9]+$ ]]; then
    echo "Error: CLIENT_COUNT must be a non-negative integer, got: $CLIENT_COUNT" >&2
    echo "Usage: $0 [OUTPUT_FILE] [CLIENT_COUNT]" >&2
    exit 1
fi

echo "Generating Docker Compose file: $OUTPUT_FILE"
echo "Client count: $CLIENT_COUNT"

cat > "$OUTPUT_FILE" <<EOL
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 ./main.py
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./server/config.ini:/app/config.ini:ro
    networks:
      - testing_net
EOL

for i in $(seq 1 "$CLIENT_COUNT"); do
  cat >> "$OUTPUT_FILE" << EOL

  client${i}:
    container_name: client${i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=${i}
    volumes:
      - ./client/config.yaml:/config.yaml:ro
      - ./.data/dataset:/.data:ro
    networks:
      - testing_net
    depends_on:
      - server
EOL
done

cat >> "$OUTPUT_FILE" << EOL

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOL

echo "Successfully created ${OUTPUT_FILE}."