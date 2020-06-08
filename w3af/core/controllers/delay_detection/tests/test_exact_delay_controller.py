"""
test_exact_delay.py

Copyright 2012 Andres Riancho

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
import unittest
import random

from mock import MagicMock, Mock

from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.url.extended_urllib import ExtendedUrllib


def generate_delays(wanted_delays, rand_range=(0, 0)):
    for delay_secs in wanted_delays:
        delay_secs += random.randint(*rand_range) / 10.0
        
        mock_response = Mock()
        mock_response.get_wait_time = Mock(return_value=delay_secs)
        
        yield mock_response


class TestExactDelay(unittest.TestCase):

    # Reminder for samples taken at ExactDelayController
    # DELAY_SECONDS = [8, 4, 9, 5, 14]

    TEST_SUITE = [
                  # Basic, very easy to pass
                  #
                  # The three 0.1 are the calls to get_average_rtt_for_mutant
                  #
                  # The 0.1 after each delay is the false positive check with
                  # the reverse payload
                  (True, (0.1, 0.1, 0.1,
                          8.1, 0.1,
                          4.1, 0.1,
                          9.1, 0.1,
                          5.1, 0.1,
                          14.1, 0.1)),
                  
                  # Basic with a +0.0 delta
                  (True, (0.1, 0.1, 0.1,
                          8.01, 0.2,
                          4.01, 0.0,
                          9.01, 0.3,
                          5.01, 0.2,
                          14.01, 0.1)),
                  
                  # Basic without controlled delays
                  (False, [0.1] * 44),

                  # Basic with server under heavy load after setup
                  # This tests the reverse payload too
                  (False, (0.1, 0.1, 0.1,
                           9.01, 9.2,
                           9.01, 9.0,
                           9.01, 9.3,
                           9.01, 9.2,
                           14.01, 14.1)),

                  # With various delays in get_average_rtt_for_mutant
                  (True, (3.1, 0.9, 0.1,
                          8.1, 0.1,
                          4.1, 0.1,
                          9.1, 0.1,
                          5.1, 0.1,
                          14.1, 0.1)),

                  (True, (3.1, 44.9, 0.1,
                          8.1, 0.1,
                          4.1, 0.1,
                          9.1, 0.1,
                          5.1, 0.1,
                          14.1, 0.1)),
    ]
    
    def test_delay_controlled(self):
        
        for expected_result, delays in self.TEST_SUITE:
            urllib = ExtendedUrllib()
            side_effect = generate_delays(delays)
            urllib.send_mutant = MagicMock(side_effect=side_effect)

            delay_obj = ExactDelay('sleep(%s)')
            
            url = URL('http://moth/?id=1')
            req = FuzzableRequest(url)
            mutant = QSMutant(req)
            mutant.set_dc(url.querystring)
            mutant.set_token(('id', 0))
            
            ed = ExactDelayController(mutant, delay_obj, urllib)
            controlled, responses = ed.delay_is_controlled()
            self.assertEqual(expected_result, controlled, delays)
    
    def test_delay_controlled_random(self):
        for expected_result, delays in self.TEST_SUITE:
            urllib = ExtendedUrllib()
            side_effect = generate_delays(delays, rand_range=(0, 2))
            urllib.send_mutant = MagicMock(side_effect=side_effect)

            delay_obj = ExactDelay('sleep(%s)')
            
            url = URL('http://moth/?id=1')
            req = FuzzableRequest(url)
            mutant = QSMutant(req)
            mutant.set_dc(url.querystring)
            mutant.set_token(('id', 0))
            
            ed = ExactDelayController(mutant, delay_obj, urllib)
            controlled, responses = ed.delay_is_controlled()
            
            # This is where we change from test_delay_controlled, the basic
            # idea is that we'll allow false negatives but no false positives
            if expected_result:
                expected_result = [True, False]
            else:
                expected_result = [False]
                
            self.assertIn(controlled, expected_result, delays)
