#!/usr/bin/python -u

from __future__ import print_function

import requests
import time
import sys


def log(message):
    print(message)
    file('rtt.log', 'a').write(message + '\n')


def send_forever(target):
    i = 0

    while True:
        start = time.time()

        # This makes sure that each URL is unique and forces the HTTP request
        # to be sent to the application server. The HTTP proxy will not be
        # able to answer.
        iter_target = target[:]
        iter_target += str(i)
        i += 1

        response = requests.get(iter_target)

        spent = time.time() - start

        msg = '[%s][%s] Received %s bytes in %.2f seconds'
        args = (i, response.status_code, len(response.text), spent)
        log(msg % args)

        time.sleep(0.5)


if __name__ == '__main__':
    try:
        target = sys.argv[1]
    except:
        print('Target URL is missing')
        print('')
        print('python w3af/core/controllers/profiling/send-request-record-rtt.py http://target.com/?rtt-measurement=')
        print('')
        sys.exit(1)

    if '?' not in target:
        print('Target URL requires a query string parameter')
        print('')
        print('python w3af/core/controllers/profiling/send-request-record-rtt.py http://target.com/?rtt-measurement=')
        print('')
        sys.exit(1)

    try:
        send_forever(target)
    except KeyboardInterrupt:
        print('Done!')
        sys.exit(0)
