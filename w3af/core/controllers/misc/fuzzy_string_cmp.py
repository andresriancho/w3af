"""
fuzzy_string_cmp.py

Copyright 2008 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import difflib
import pprint


def relative_distance_boolean(a_str, b_str, threshold=0.6):
    """
    Indicates if the strings to compare are similar enough. This (optimized)
    function is equivalent to the expression:
        relative_distance(x, y) > threshold

    :param a_str: A string object
    :param b_str: A string object
    :param threshold: Float value indicating the expected "similarity". Must be
                      0 <= threshold <= 1.0
    :return: A boolean value
    """
    if threshold == 0:
        return True
    elif threshold == 1.0:
        return a_str == b_str

    # First we need b_str to be the longer of both
    if len(b_str) < len(a_str):
        a_str, b_str = b_str, a_str

    alen = len(a_str)
    blen = len(b_str)

    if blen == 0 or alen == 0:
        return alen == blen

    if blen == alen and a_str == b_str and threshold <= 1.0:
        return True

    if threshold > upper_bound_similarity(a_str, b_str):
        return False
    else:
        # Bad, we can't optimize anything here
        return threshold <= difflib.SequenceMatcher(None, a_str, b_str).quick_ratio()


def upper_bound_similarity(a, b):
    return (2.0*len(a))/(len(a)+len(b))


def fuzzy_equal(a_str, b_str, threshold=0.6):
    """
    Indicates if the 'similarity' index between strings
    is *greater equal* than 'threshold'. See 'relative_distance_boolean'.
    """
    return relative_distance_boolean(a_str, b_str, threshold)


def fuzzy_not_equal(a_str, b_str, threshold=0.6):
    """
    Indicates if the 'similarity' index between strings
    is *less than* 'threshold'
    """
    return not relative_distance_boolean(a_str, b_str, threshold)


def relative_distance(a_str, b_str):
    """
    Measures the "similarity" of the strings.

    Depends on the algorithm we finally implement, but usually a return value
    over 0.6 means the strings are close matches.

    :param a_str: A string object
    :param b_str: A string object
    :return: A float with the distance
    """
    set_a = set(a_str.split(' '))
    set_b = set(b_str.split(' '))

    if min(len(set_a), len(set_b)) in (0, 1):
        #
        #   This is a rare case, where the http response body is one long
        #   non-space separated string.
        #
        return difflib.SequenceMatcher(None, a_str, b_str).quick_ratio()

    return 1.0 * len(set_a.intersection(set_b)) / max(len(set_a), len(set_b))


if __name__ == "__main__":
    # These tests should be reallocated in a test module.
    """import time
    import urllib2

    performance_tests = []

    #performance_tests.append(('a'*25000,'a'*25000,0.999 ))
    #performance_tests.append(('a'*12000, 'a'*25000, 0.9999))
    #performance_tests.append(('a'*20000, 'a'*25000, 0.1))

    google = urllib2.urlopen("http://www.google.com").read()
    google2 = urllib2.urlopen("http://www.google.co.uk/").read()

    yahoo = urllib2.urlopen("http://www.yahoo.com/").read()
    yahoo2 = urllib2.urlopen("http://uk.yahoo.com/").read()

    bing = urllib2.urlopen("http://www.bing.com/").read()
    bing2 = urllib2.urlopen("http://www.bing.com/?cc=gb").read()


    #True
    performance_tests.append((google, google, 0.99999999))
    performance_tests.append((google2, google2, 0.99999999))
    performance_tests.append((yahoo, yahoo, 0.99999999))
    performance_tests.append((yahoo2, yahoo2, 0.99999999))
    performance_tests.append((bing, bing, 0.99999999))
    performance_tests.append((bing2, bing2, 0.99999999))

    #False
    performance_tests.append((bing, google, 0.99999999))
    performance_tests.append((bing, yahoo, 0.99999999))
    performance_tests.append((yahoo, google, 0.99999999))
    performance_tests.append((yahoo2, google, 0.99999999))
    performance_tests.append((bing2, google, 0.99999999))
    performance_tests.append((yahoo, google2, 0.99999999))

    #True
    performance_tests.append((google, google, 0.1))
    performance_tests.append((google2, google2, 0.1))
    performance_tests.append((yahoo, yahoo, 0.1))
    performance_tests.append((yahoo2, yahoo2, 0.1))
    performance_tests.append((bing, bing, 0.1))
    performance_tests.append((bing2, bing2, 0.1))

    #False
    performance_tests.append((bing, google, 0.6))
    performance_tests.append((bing, yahoo, 0.6))
    performance_tests.append((yahoo, google, 0.6))
    performance_tests.append((yahoo2, google, 0.6))
    performance_tests.append((bing2, google, 0.6))
    performance_tests.append((yahoo, google2, 0.6))

    start = time.time()
    relative_distance_boolean('a', 'a', 1.0)
    needed = time.time() - start
    print "Setup of bounds took " + str(needed)

    #performance tests
    numOfTests = 20
    numOfOverallTests = 4

    boolean_time_sum = 0
    original_time_sum = 0

    for i in range(0, numOfOverallTests):

        boolean_win_count = 0
        original_win_count = 0

        for e, d, f in performance_tests:
            print e[:40]
            print d[:40]
            k = '?'
            start = time.time()
            for i in range(0, numOfTests):
                relative_distance_boolean(e, d, f)
            end = time.time()
            k = relative_distance_boolean(e, d, f)
            boolean_time = end - start
            boolean_time_sum += boolean_time
            print "   boolean (" + str(k) + ") :", boolean_time

            k = '?'
            start = time.time()
            for i in range(0, numOfTests):
                relative_distance(e, d) >= f
            end = time.time()
            k = relative_distance(e, d) >= f
            original_time = end - start
            original_time_sum += original_time
            print "   original (" + str(k) + ") :", original_time

            if original_time > boolean_time:
                boolean_win_count += 1
            else:
                original_win_count += 1

        print 'boolean win: ' + str(boolean_win_count) + ', original win: ' + str(original_win_count)

    print '-----------'
    print 'Boolean:', boolean_time_sum / numOfOverallTests
    print 'Original:', original_time_sum / numOfOverallTests
    """

