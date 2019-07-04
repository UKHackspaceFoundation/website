#!/bin/sh

# Script used to log in to the Docker registry with Travis.

echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
