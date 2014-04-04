#!/bin/bash -x

if [ ! -d "pico-wavsep" ]; then
    git clone https://github.com/andresriancho/pico-wavsep.git
fi

# Update to the latest revision
cd pico-wavsep/
git pull
git checkout master
#git log -n 1

# Let the rest of the world know where we'll listen
echo 'localhost:8098' > /tmp/wavsep.txt

# The service itself is started in circle.yml
