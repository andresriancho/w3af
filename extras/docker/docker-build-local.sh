#!/bin/bash

# This scripts builds Docker image from actual source code, so you can access it
# as andresriancho/w3af:source
# Use it if for any reasons you want to run w3af inside Docker

cp Dockerfile ../../
cp .dockerignore ../../

cd ../../

docker build -t andresriancho/w3af:source .

rm -rf Dockerfile
rm -rf .dockerignore

cd extras/docker/
