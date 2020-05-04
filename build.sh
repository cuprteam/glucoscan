#!/usr/bin/env sh

echo "Building docker image for glucoscan"
set -ex

docker build -t glucoscan .

set +ex
echo "Building docker image for glucoscan FINISHED."