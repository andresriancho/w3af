"""
test_fingerprint_404_perf.py

Copyright 2019 Andres Riancho

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
import os
import time
import random
import unittest

from mock import Mock


from w3af import ROOT_PATH
from w3af.core.controllers.core_helpers.fingerprint_404 import Fingerprint404
from w3af.tests.helpers.parse_http_log import iter_http_request_responses


class TestFingerprint404Perf(unittest.TestCase):

    HTTP_FILE = os.path.join(ROOT_PATH, '..', 'scan-logs', 'kryptera-ktCKJ.http')
    MAX_REQUEST_RESPONSE = 2000

    RECORDED_200_EVERY = 18
    MAX_RECORDED_200 = 25

    MAX_RECORDED_404 = 25
    RECORDED_404_EVERY = 17

    CACHE_TEST_EVERY = 50
    CACHE_TESTS = 5

    def test_should_grep_speed(self):
        """
        This method tests the performance of the _is_404_complex() method
        from the Fingerprint404 class.

        This method is usually run as:

            kernprof -o nose.lprof -v -l nosetests -s -v w3af/core/controllers/core_helpers/not_found/tests/test_fingerprint_404_perf.py

        Remember to:

            * Specify a valid file in HTTP_FILE (generated during a scan)
            * Decorate the methods you want to analyze with @profile
        """
        if not os.path.exists(self.HTTP_FILE):
            return

        rnd = random.Random()
        rnd.seed(1)

        recorded_404s = []
        recorded_200s = []
        mock_404_response = None

        def mock_get(url, **kwargs):
            # 100ms delay to simulate the network
            time.sleep(0.1)

            return mock_404_response

        urllib = Mock()
        urllib.GET = mock_get

        fingerprint_404 = Fingerprint404()
        fingerprint_404.set_url_opener(urllib)

        for count, (request, response) in enumerate(iter_http_request_responses(self.HTTP_FILE)):

            if response.get_code() == 404:
                if len(recorded_404s) <= self.MAX_RECORDED_404:
                    recorded_404s.append(response)

            if response.get_code() != 404:
                if len(recorded_200s) <= self.MAX_RECORDED_200:
                    recorded_200s.append(response)

            if len(recorded_404s):
                if count % self.RECORDED_404_EVERY == 0:
                    mock_404_response = rnd.choice(recorded_404s)

            elif len(recorded_200s):
                if count % self.RECORDED_200_EVERY == 0:
                    mock_404_response = rnd.choice(recorded_200s)

            if mock_404_response is None:
                mock_404_response = response

            fingerprint_404._is_404_complex(response)

            if count % self.CACHE_TEST_EVERY == 0:
                for _ in xrange(self.CACHE_TESTS):
                    fingerprint_404._is_404_complex(response)

            if count >= self.MAX_REQUEST_RESPONSE:
                break

            mock_404_response = None
