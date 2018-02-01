#!/bin/bash

set -x
set -e

cp Dockerfile ../../
cp .dockerignore ../../

cd ../../

if [ $# -eq 1 ]; then
    TAG=$1
else
    echo "Image tag argument is required in the format REPOSITORY/IMAGE:TAG (andresriancho/w3af:stable)."
    exit 1
fi

docker build -t ${TAG} .

docker push ${TAG}

rm -rf Dockerfile
rm -rf .dockerignore

cd extras/docker/
