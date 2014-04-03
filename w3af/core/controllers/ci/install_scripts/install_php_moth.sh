#!/bin/bash -x

if [ ! -d "php-moth" ]; then
    git clone git@github.com:andresriancho/php-moth.git
fi

# Update to the latest revision
cd php-moth/
git pull
git checkout master

# Let the rest of the world know where we'll listen
echo 'localhost:9009' > /tmp/php_moth.txt

# The service itself is started in circle.yml