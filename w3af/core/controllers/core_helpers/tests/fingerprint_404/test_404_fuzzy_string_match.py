# -*- coding: UTF-8 -*-
"""
test_404_fuzzy_string_match.py

Copyright 2014 Andres Riancho

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
from __future__ import division

import unittest
import os
import shelve
import time
import re

from nose.plugins.skip import SkipTest

from w3af.core.controllers.misc.levenshtein import relative_distance_ge
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.core_helpers.fingerprint_404 import (IS_EQUAL_RATIO,
                                                                get_clean_body)

FAILED_FILENAME = 'not-ex1st.html'


class Test404FuzzyStringMatch(unittest.TestCase):
    """
    This is written as a test to be able to run it easily using nosetests,
    but is mostly a simple check to verify the following:

        * relative_distance_ge is too slow

        * The patch I'm working on can distinguish 404s just as good as the slow
        relative_distance_ge, and is much faster.

    :see: https://github.com/andresriancho/w3af/issues/2072
    """
    not_exists_data = None
    empty_headers = Headers()

    def setUp(self):
        test_dir = os.path.dirname(os.path.realpath(__file__))
        shelve_file = os.path.join(test_dir, 'data.shelve')

        if not os.path.exists(shelve_file):
            raise SkipTest('No shelve, get it from w3af-misc repository.')

        self.not_exists_data = shelve.open(shelve_file)

    def tearDown(self):
        if self.not_exists_data is not None:
            self.not_exists_data.close()

    def _create_http_response(self, domain, body, is_404):
        url = URL('http://%s/%s' % (domain, FAILED_FILENAME if is_404 else ''))
        resp = HTTPResponse(200, body, self.empty_headers, url, url)
        return resp

    def generic_fuzzy_string_diff_runner(self, fuzzy_func, ratio):
        """
        Generic runner for fuzzy string diff
        """
        failed_domains = set()
        total = 0
        start = time.time()

        for domain, (ok, not_exists) in self.not_exists_data.iteritems():
            total += 1

            ok_resp = self._create_http_response(domain, ok, False)
            not_exists_resp = self._create_http_response(domain, not_exists,
                                                         True)

            clean_body_ok = get_clean_body(ok_resp)
            clean_body_not_exists = get_clean_body(not_exists_resp)

            if fuzzy_func(clean_body_not_exists, clean_body_ok, ratio):
                failed_domains.add(domain)

        end = time.time()

        perc_fail = len(failed_domains) / total
        func_name = fuzzy_func.__name__

        print('%s fail rate: %s' % (func_name, perc_fail))
        print('Total time: %ss' % (end-start))
        print('Analyzed samples: %s' % total)

        output = '/tmp/%s.txt' % func_name
        output_fh = file(output, 'w')
        for domain in sorted(failed_domains):
            output_fh.write('%s\n' % domain)

        print('Failed domains stored at %s' % output)
        #
        #   Hah! At some point I thought this was possible!
        #
        #self.assertEqual(failed_domains, set())

    def test_relative_distance_ge(self):
        """
        Test the optimized call to difflib: relative_distance_ge

        relative_distance_ge fail rate: 0.138044371405
        Total time: 12.5121450424s
        Analyzed samples: 1217
        """
        self.generic_fuzzy_string_diff_runner(relative_distance_ge,
                                              IS_EQUAL_RATIO)

    def test_jellyfish_jaro(self):
        """
        Yet another ugly surprise, jaro_distance takes ages to run.
        """
        # Import it here to avoid issues with missing dependencies in CI
        import jellyfish

        def jelly_fuzzy(str_a, str_b, ratio):
            str_a = str_a.replace('\0', '')
            str_b = str_b.replace('\0', '')
            return jellyfish.jaro_distance(str_a, str_b) > ratio

        self.generic_fuzzy_string_diff_runner(jelly_fuzzy, IS_EQUAL_RATIO)

    def test_jellyfish_levenshtein_distance(self):
        """
        That's an ugly surprise! jellyfish.levenshtein_distance seems to have
        a memory leak somewhere.
        """
        raise SkipTest('This one raises a MemoryError')

        # Import it here to avoid issues with missing dependencies in CI
        import jellyfish

        def jelly_fuzzy(str_a, str_b, ratio):
            str_a = str_a.replace('\0', '')
            str_b = str_b.replace('\0', '')
            minl = min(len(str_a), len(str_b))
            return (jellyfish.levenshtein_distance(str_a, str_b) / minl) > ratio

        self.generic_fuzzy_string_diff_runner(jelly_fuzzy, IS_EQUAL_RATIO)

    def test_tokenized_set(self):
        """
        tokenized_set fail rate: 0.120788824979
        Total time: 3.8881289959s
        Analyzed samples: 1217
        """
        def tokenized_set(str_a, str_b, ratio):
            set_a = set(str_a.split(' '))
            set_b = set(str_b.split(' '))
            maxl = max(len(set_a), len(set_b))
            return (len(set_a.intersection(set_b)) / maxl) > ratio

        self.generic_fuzzy_string_diff_runner(tokenized_set, IS_EQUAL_RATIO)

    def test_tokenized_set_str_hash(self):
        """
        I thought that maybe the set intersection would be faster with hashes:
        wrong!
            tokenized_set fail rate: 0.120689655172
            Total time: 6.78003907204s
            Analyzed samples: 1218
        """
        def tokenized_set(str_a, str_b, ratio):
            set_a = set(hash(x) for x in str_a.split(' '))
            set_b = set(hash(x) for x in str_b.split(' '))
            maxl = max(len(set_a), len(set_b))
            return (len(set_a.intersection(set_b)) / maxl) > ratio

        self.generic_fuzzy_string_diff_runner(tokenized_set, IS_EQUAL_RATIO)

    def test_tokenized_set_split_re(self):
        """
        Expected this one to have a lower fail rate, and to be slower:
            tokenized_set fail rate: 0.124794745484
            Total time: 14.5680158138s
            Analyzed samples: 1218

        It was slower, but no improvement on fail rate.
        """
        def tokenized_set(str_a, str_b, ratio):
            set_a = set(re.split('(\w+)', str_a))
            set_b = set(re.split('(\w+)', str_b))
            maxl = max(len(set_a), len(set_b))
            return (len(set_a.intersection(set_b)) / maxl) > ratio

        self.generic_fuzzy_string_diff_runner(tokenized_set, IS_EQUAL_RATIO)

    def test_tokenized_set_large(self):
        """
        tokenized_set fail rate: 0.117405582923
        Total time: 5.8883600235s
        Analyzed samples: 1218
        """
        def tokenized_set(str_a, str_b, ratio):
            set_a = set(x for x in str_a.split(' ') if len(x) > 12)
            set_b = set(x for x in str_b.split(' ') if len(x) > 12)
            maxl = max(len(set_a), len(set_b))

            intersect = set_a.intersection(set_b)
            if not intersect:
                return False

            return (len(intersect) / maxl) > ratio

        self.generic_fuzzy_string_diff_runner(tokenized_set, IS_EQUAL_RATIO)

    def test_tokenized_set_small(self):
        """
        tokenized_set fail rate: 0.122331691297
        Total time: 6.38607501984s
        Analyzed samples: 1218
        """
        def tokenized_set(str_a, str_b, ratio):
            set_a = set(x for x in str_a.split(' ') if len(x) < 12)
            set_b = set(x for x in str_b.split(' ') if len(x) < 12)
            maxl = max(len(set_a), len(set_b))

            intersect = set_a.intersection(set_b)
            if not intersect:
                return False

            return (len(intersect) / maxl) > ratio

        self.generic_fuzzy_string_diff_runner(tokenized_set, IS_EQUAL_RATIO)

    def test_tokenized_set_split_tag(self):
        """
        Splitting by "<" instead of " " seems to make more sense:
            * Lower run time
            * Lower fail rate

        tokenized_set fail rate: 0.115763546798
        Total time: 2.94191193581s
        Analyzed samples: 1218

        There is a reason for this... "<" is less common than " " in the
        response bodies:
            [(' ', 21827575),
             ('e', 7560435),
             ('a', 7394690),
             ('t', 7115405),
             ('i', 6285118),
             ('s', 5746931),
             ('"', 5272311),
             ('o', 5011207),
             ('l', 4831219),
             ('n', 4732762),
             ('r', 4701036),
             ('/', 4417755),
             ('c', 4003959),
             ('d', 3420064),
             ('p', 3269927),
             ('>', 3258488),
             ('<', 3255475),
             ('=', 2858727),
             ('\t', 2849400),
             ('h', 2766599)]

        So when we split by a less common char, we're "moving towards" the
        trivial string equal comparison. As an example, splitting by "<dnfslsk"
        would return 0% fail rate.
        """
        def tokenized_set_split_tag(str_a, str_b, ratio):
            set_a = set(str_a.split('<dnfslsk'))
            set_b = set(str_b.split('<dnfslsk'))
            maxl = max(len(set_a), len(set_b))
            return (len(set_a.intersection(set_b)) / maxl) > ratio

        self.generic_fuzzy_string_diff_runner(tokenized_set_split_tag,
                                              IS_EQUAL_RATIO)
