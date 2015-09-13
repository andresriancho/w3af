#!/usr/bin/env python

import sys
import time
import urllib2

LOOPS = 25
DELAY = 1

TEST_DEPENDENCIES = ['http://127.0.0.1:8000',
                     'https://127.0.0.1:8001',
                     'http://127.0.0.1:8899',
                     'http://127.0.0.1:9008',
                     'http://127.0.0.1:9009',
                     'http://127.0.0.1:8998',
                     'http://127.0.0.1:8098']

is_available = []

for _ in xrange(LOOPS):
    time.sleep(DELAY)

    for url in TEST_DEPENDENCIES:
        if url in is_available:
            continue

        try:
            urllib2.urlopen(url)
        except Exception, e:
            print('%s is offline (%s)' % (url, e.__class__.__name__))
        else:
            print('%s is ready' % url)
            is_available.append(url)

if len(is_available) != len(TEST_DEPENDENCIES):
    print('Timeout waiting for test dependencies!')
    sys.exit(1)
