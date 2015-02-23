#!/bin/sh

set -x
set -e

cp Dockerfile ../../
cp .dockerignore ../../

cd ../../
COMMIT=`git rev-parse --short HEAD`
sudo docker build -t andresriancho/w3af:${COMMIT} .

rm -rf Dockerfile
rm -rf .dockerignore

cd extras/docker/

