#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p data logs

# Build and start the container
docker-compose up -d --build

# Show logs
docker-compose logs -f 