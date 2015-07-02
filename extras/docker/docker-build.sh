#!/bin/bash

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

NEW_TAG=`docker-tag-naming bump andresriancho/w3af ${ENV} --commit-id ${CIRCLE_SHA1:0:7}`

docker build -t andresriancho/w3af:${ENV} .
docker tag andresriancho/w3af:${ENV} andresriancho/w3af:${NEW_TAG}

docker push andresriancho/w3af:${ENV}
docker push andresriancho/w3af:${NEW_TAG}

rm -rf Dockerfile
rm -rf .dockerignore

cd extras/docker/

