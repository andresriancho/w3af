#!/bin/bash

set -x
set -e

cp Dockerfile ../../
cp .dockerignore ../../

cd ../../


if [ $# -eq 1 ]; then
    ENV=$1
else
    echo "Build environment name argument is required (./docker-build.sh develop)"
    exit 1
fi

docker-tag-naming bump andresriancho/w3af ${ENV} --commit-id ${CIRCLE_SHA1:0:7} > /tmp/new-w3af-docker-tag.txt
NEW_TAG=`cat /tmp/new-w3af-docker-tag.txt`

docker build -t andresriancho/w3af:${ENV} .
docker tag andresriancho/w3af:${ENV} andresriancho/w3af:${NEW_TAG}

docker push andresriancho/w3af:${ENV}
docker push andresriancho/w3af:${NEW_TAG}

rm -rf Dockerfile
rm -rf .dockerignore

cd extras/docker/

