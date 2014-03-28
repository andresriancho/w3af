#!/bin/bash -x

if [ ! -d "wivet" ]; then
    git clone git@github.com:bedirhan/wivet.git
fi

# Update to the latest revision
cd wivet/
git pull
git checkout master

# Let the rest of the world know where we'll listen
echo 'localhost:8899' > /tmp/wivet.txt

# The service itself is started in circle.yml