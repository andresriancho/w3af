#!/bin/sh

set -x
set -e

cp Dockerfile ../../
cp .dockerignore ../../

cd ../../


if [ $# -eq 1 ]; then
    ENV=$1
else
    echo "Environment argument is required"
    exit 1
fi

sudo docker build -t andresriancho/w3af:${CIRCLE_SHA1:0:7}-${ENV} .
sudo docker tag andresriancho/w3af:${CIRCLE_SHA1:0:7}-${ENV} andresriancho/w3af:${ENV}

rm -rf Dockerfile
rm -rf .dockerignore

cd extras/docker/

