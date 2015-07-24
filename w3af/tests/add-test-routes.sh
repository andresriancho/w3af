#!/usr/bin/env bash

set -e
set -x

echo "127.0.0.1:8000" > /tmp/moth-http.txt
echo "127.0.0.1:8001" > /tmp/moth-https.txt
echo "127.0.0.1:8899" > /tmp/wivet.txt
echo "127.0.0.1:9009" > /tmp/php-moth.txt
echo '127.0.0.1:8998' > /tmp/sqlmap-testenv.txt
echo '127.0.0.1:8998' > /tmp/sqlmap-testenv.txt
echo '127.0.0.1:8098' > /tmp/wavsep.txt
