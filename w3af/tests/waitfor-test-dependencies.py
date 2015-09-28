#!/usr/bin/env python

import sys
import time
import urllib2

LOOPS = 25
DELAY = 1

WAVSEP_TEST_URL = ('http://127.0.0.1:8098/wavsep/active/SQL-Injection/'
                   'SInjection-Detection-Evaluation-GET-200Error/'
                   'Case01-InjectionInLogin-String-LoginBypass-With200Errors.jsp?'
                   'username=%27or%277%27=%277&password=%27or%277%27=%277')

TEST_DEPENDENCIES = [('http://127.0.0.1:8000', None),
                     ('https://127.0.0.1:8001', None),
                     ('http://127.0.0.1:8899', None),
                     ('http://127.0.0.1:9008', None),
                     ('http://127.0.0.1:9009', None),
                     ('http://127.0.0.1:8998', None),
                     (WAVSEP_TEST_URL, 'hello user1'),
                     ('http://127.0.0.1:8090', None)]

is_available = []

for _ in xrange(LOOPS):
    time.sleep(DELAY)

    for url, match_string in TEST_DEPENDENCIES:
        if url in is_available:
            continue

        try:
            content = urllib2.urlopen(url).read()
        except Exception, e:
            print('%s is offline (%s)' % (url, e.__class__.__name__))
        else:
            if match_string is None:
                print('%s is UP' % url)
                is_available.append(url)

            elif match_string in content:
                print('%s is UP and matches string' % url)
                is_available.append(url)

            else:
                print('%s is UP but string does NOT match' % url)


if len(is_available) != len(TEST_DEPENDENCIES):
    print('Timeout waiting for test dependencies!')
    sys.exit(1)
