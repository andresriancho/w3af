'''
levenshtein.py

Copyright 2008 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''

import difflib
import pprint

from upper_bounds import UPPER_BOUNDS

def relative_distance_boolean(a_str, b_str, threshold=0.6):
    '''
    Indicates if the strings to compare are enough "similar". This (optimized)
    function is equivalent to the expression:
    relative_distance(x, y) > threshold
    
    @param a_str: A string object
    @param b_str: A string object
    @param threshold: Float value indicating the expected "similarity". Must be 0 <= threshold <= 1.0
    @return: A boolean value
    '''

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

    ratio = float(blen) / alen

    last_ratio, last_bound = UPPER_BOUNDS[-1]

    if threshold < last_bound:
        # Bad, we can't optimize anything here
        return relative_distance(a_str, b_str) >= threshold
    else:
        if last_ratio < ratio:
            # Good, we know the upper bound
            return False
        else:
            # We have to step through
            for size_ratio, bound in UPPER_BOUNDS:
                if size_ratio > ratio:
                    # Bad: we have to do the relative_distance
                    return relative_distance(a_str, b_str) >= threshold
                elif bound < threshold:
                    # Good: We found an upper bound
                    return False


def relative_distance_ge(a_str, b_str, threshold=0.6):
    '''
    Indicates if the 'similarity' index between strings
    is *greater equal* than 'threshold'. See 'relative_distance_boolean'.
    '''
    return relative_distance_boolean(a_str, b_str, threshold)

def relative_distance_lt(a_str, b_str, threshold=0.6):
    '''
    Indicates if the 'similarity' index between strings
    is *less than* 'threshold'
    '''
    return not relative_distance_boolean(a_str, b_str, threshold)


def relative_distance(a_str, b_str):
    '''
    Measures the "similarity" of the strings. A return value value over 0.6
    means the strings are close matches.
    
    @param a_str: A string object
    @param b_str: A string object
    @return: A float with the distance
    '''
    return difflib.SequenceMatcher(None, a_str, b_str).quick_ratio()


def _generate_upper_bounds():
    '''
    This function can be used to produce new upper bounds,
    but shouldn't be used in productive code. Simply run this
    command once and then hardcode the list.
    '''

    left_max = 40
    right_max = 30

    UPPER_BOUNDS = set()
    UPPER_BOUNDS.add((1.0, 1.0))

    def addToBounds(a, b):
        size = float(len(b)) / len(a)
        upper_bound = relative_distance(a, b)
        UPPER_BOUNDS.add((size, upper_bound))

    for k in range(1, left_max):
        for i in range(1, right_max):
            if k == i == 1:
                continue
            atest = 'm' * k
            btest = 'm' * k + 'm' * (i - 1)
            addToBounds(atest, btest)

    # Remove duplicates
    UPPER_BOUNDS = list(UPPER_BOUNDS)

    # Sort
    UPPER_BOUNDS.sort(lambda x, y: cmp(x[0], y[0]))

    fp = file("upper_bounds.py", "w")
    fp.write("UPPER_BOUNDS = ")
    pprint.pprint(UPPER_BOUNDS, fp)
    fp.close()


if __name__ == "__main__":
    # Uncomment next function call to generate 'upper_bounds.py' module
    #_generate_upper_bounds()

    # This tests should be reallocated in a test module.
    '''import time
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



    acceptance_tests = []
    acceptance_tests.extend(performance_tests)
    acceptance_tests.append(('a', 'a', 1.0))
    acceptance_tests.append(('a', 'a', 0.1))
    acceptance_tests.append(('a', 'a', 0.0))

    acceptance_tests.append(('a', 'b', 1.0))
    acceptance_tests.append(('a', 'b', 0.1))
    acceptance_tests.append(('a', 'b', 0.0))

    acceptance_tests.append(('a', 'ab', 1.0))
    acceptance_tests.append(('a', 'ab', 0.1))

    acceptance_tests.append(('a', 'b', 0.0000000000000000001))
    acceptance_tests.append(('a', 'b' * 100, 1.0))

    acceptance_tests.append(('a', 'ab', 0.66666666666))
    acceptance_tests.append(('a', 'aab', 0.5))
    acceptance_tests.append(('a', 'aaab', 0.4))
    acceptance_tests.append(('a', 'aaaab', 0.33333333333333333333333333333333333333333333333333333333))

    acceptance_tests.append(('a' * 25, 'a', 1.0))
    acceptance_tests.append(('aaa', 'aa', 1.0))
    acceptance_tests.append(('a', 'a', 1.0))

    acceptance_tests.append(('a' * 25, 'a', 0.076923076923076927))
    acceptance_tests.append(('aaa', 'aa', 0.8))

    acceptance_tests.append(('a', 'a', 0.0))


    start = time.time()
    relative_distance_boolean('a', 'a', 1.0)
    needed = time.time() - start
    print "Setup of bounds took " + str(needed)


    #acceptance tests
    for e, d, f in acceptance_tests:
        res1 = relative_distance_boolean(e, d, f)
        res2 = relative_distance(e, d) >= f
        if res1 == res2:
            print "PASS", res1
        else:
            print "FAIL: ", e, d, f
            print res1, res2
            exit()


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

'''
