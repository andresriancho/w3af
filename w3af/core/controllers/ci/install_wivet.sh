#!/bin/bash -x

if [ ! -d "wivet" ]; then
    git clone git@github.com:andresriancho/wivet.git
fi

# Update to the latest revision
cd wivet/
git pull
git checkout feature/clear-stats

# Setup the database
mysql -u ubuntu < wivet.sql

# Let the rest of the world know where we'll listen
echo 'localhost:8899' > /tmp/wivet.txt
