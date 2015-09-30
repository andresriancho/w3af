#!/usr/bin/env bash

set -e
set -x

# Make sure only root can run our script
if [ "$(id -u)" != "0" ] && [ -z "$CIRCLECI" ]; then
   echo "This script must be run as root or in CircleCI" 1>&2
   exit 1
fi

# Need root in most dev environments, in CI we just run using sudo because
# there is no password required
#
# Only add the line to /etc/hosts if it's not there already
grep -q -F '127.0.0.1 moth' /etc/hosts || echo '127.0.0.1 moth' | sudo tee -a /etc/hosts

# Routes to be read by python code + tests
echo "127.0.0.1:8000" > /tmp/moth-http.txt
echo "127.0.0.1:8001" > /tmp/moth-https.txt
echo "127.0.0.1:8899" > /tmp/wivet.txt
echo "127.0.0.1:9008" > /tmp/w3af-moth.txt
echo "127.0.0.1:9009" > /tmp/php-moth.txt
echo '127.0.0.1:8998' > /tmp/sqlmap-testenv.txt
echo '127.0.0.1:8998' > /tmp/sqlmap-testenv.txt
echo '127.0.0.1:8098' > /tmp/wavsep.txt
echo '127.0.0.1:8090' > /tmp/mcir.txt
