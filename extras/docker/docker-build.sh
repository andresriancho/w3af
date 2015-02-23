#!/bin/sh

set -x
set -e

cp Dockerfile ../../
cp .dockerignore ../../

cd ../../


if [ $# -eq 1 ]; then
    TAG=$1
else
    TAG=`git rev-parse --short HEAD`
fi

sudo docker build -t andresriancho/w3af:${TAG} .

rm -rf Dockerfile
rm -rf .dockerignore

cd extras/docker/

