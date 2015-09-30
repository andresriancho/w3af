#!/usr/bin/env python

import sys
import time
import urllib2

LOOPS = 25
DELAY = 1
STABLE_LOOPS = 5

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


def is_online(url, match_string):
    try:
        content = urllib2.urlopen(url).read()
    except urllib2.HTTPError, e:
        content = e.read()
    except Exception, e:
        print('%s is offline (%s)' % (url, e.__class__.__name__))
        return False

    if match_string is None:
        print('%s is UP' % url)
        return True

    elif match_string in content:
        print('%s is UP and matches string' % url)
        return True

    else:
        print('%s is UP but string does NOT match' % url)

    return False


def waitfor_test_dependencies():
    print('Waiting for dependencies to be up...\n\n')
    is_available = []

    for _ in xrange(LOOPS):
        time.sleep(DELAY)

        for url, match_string in TEST_DEPENDENCIES:
            if url in is_available:
                continue

            if is_online(url, match_string):
                is_available.append(url)

    if len(is_available) != len(TEST_DEPENDENCIES):
        print('Timeout waiting for test dependencies!')
        sys.exit(1)

    return True


def wait_until_stable():
    print('\n\nWaiting for dependencies to be stable...\n\n')
    test_results = {}

    for _ in xrange(LOOPS):
        time.sleep(DELAY)

        for url, match_string in TEST_DEPENDENCIES:
            if is_online(url, match_string):
                if url in test_results:
                    test_results[url] += 1
                else:
                    test_results[url] = 1
            else:
                test_results[url] = 0

    up_count_summary = []

    for up_count in test_results.itervalues():
        up_count_summary.append(up_count >= STABLE_LOOPS)

    if not all(up_count_summary):
        print('Test dependencies are not stable')
        sys.exit(1)

    return True

if __name__ == '__main__':
    waitfor_test_dependencies()
    wait_until_stable()
