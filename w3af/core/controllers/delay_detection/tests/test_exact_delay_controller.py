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


def generate_delays(wanted_delays, rand_range=(0, 0)):
    for delay_secs in wanted_delays:
        delay_secs += random.randint(*rand_range) / 10.0
        
        mock_response = Mock()
        mock_response.get_wait_time = Mock(return_value=delay_secs)
        
        yield mock_response


class TestExactDelay(unittest.TestCase):

    # Reminder for samples taken at ExactDelayController
    # DELAY_SECONDS = [12, 8, 15, 20, 4, 4, 4, 6, 3, 8, 4]

    TEST_SUITE = [
                  # Basic, very easy to pass
                  # The three 0.1 are the calls to get_original_time
                  (True, (0.1, 0.1, 0.1, 12.5,
                          0.1, 0.1, 0.1, 8.1,
                          0.1, 0.1, 0.1, 15.1,
                          0.1, 0.1, 0.1, 20.2,
                          0.1, 0.1, 0.1, 4.4,
                          0.1, 0.1, 0.1, 4.2,
                          0.1, 0.1, 0.1, 4.0,
                          0.1, 0.1, 0.1, 6.2,
                          0.1, 0.1, 0.1, 3.3,
                          0.1, 0.1, 0.1, 8.0,
                          0.1, 0.1, 0.1, 4.9)),
                  
                  # Basic with a +0.1 delta
                  (True, (0.1, 0.1, 0.1, 12.1,
                          0.1, 0.1, 0.1, 8.1,
                          0.1, 0.1, 0.1, 15.1,
                          0.1, 0.1, 0.1, 20.1,
                          0.1, 0.1, 0.1, 4.1,
                          0.1, 0.1, 0.1, 4.1,
                          0.1, 0.1, 0.1, 4.1,
                          0.1, 0.1, 0.1, 6.1,
                          0.1, 0.1, 0.1, 3.1,
                          0.1, 0.1, 0.1, 8.1,
                          0.1, 0.1, 0.1, 4.1)),
                  
                  # Basic without controlled delays
                  (False, [0.1] * 44),

                  # Basic with server under heavy load after setup
                  (False, (0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5)),

                  # Basic with server under random heavy load after setup
                  (False, (0, 0, 0, 5,
                           0, 0, 0, 2,
                           0, 0, 0, 2,
                           0, 0, 0, 8,
                           0, 0, 0, 2,
                           0, 0, 0, 3,
                           0, 0, 0, 5,
                           0, 0, 0, 7,
                           0, 0, 0, 3,
                           0, 0, 0, 4,
                           0, 0, 0, 4)),

                  # Basic with server under random heavy load after setup
                  (False, (0.1, 0.2, 0.2, 5,
                           0.1, 0.2, 0.2, 2,
                           0.1, 0.2, 0.2, 2,
                           0.1, 0.2, 0.2, 2,
                           0.1, 0.2, 0.2, 5,
                           0.1, 0.2, 0.2, 4,
                           0.1, 0.2, 0.2, 2,
                           0.1, 0.2, 0.2, 1,
                           0.1, 0.2, 0.2, 6,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 8)),

                  # Basic with server under random heavy load after setup
                  (False, (0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7)),

                  # Case explained in this commit:
                  # https://github.com/andresriancho/w3af/commit/dbef5480db6c09ec3a3493f544c108f61155f75c
                  (True, (0.1, 0.2, 0.2, 12,
                          0.1, 0.2, 0.2, 8,
                          0.1, 0.2, 0.2, 19,
                          0.1, 0.2, 0.2, 22,
                          0.1, 0.2, 0.2, 6,
                          0.1, 0.2, 0.2, 6,
                          0.1, 0.2, 0.2, 6,
                          0.1, 0.2, 0.2, 8,
                          0.1, 0.2, 0.2, 3,
                          0.1, 0.2, 0.2, 8,
                          0.1, 0.2, 0.2, 4)),

                  # With various delays in the setup phase
                  (True, (0, 0.2, 0, 12.8,
                          0, 0.1, 0.15, 8.1,
                          0, 0.2, 0, 15.1,
                          0, 0.2, 0, 20.1,
                          0, 0.2, 0, 4.1,
                          0, 0.2, 0, 4.1,
                          0, 0.2, 0, 4.1,
                          0, 0.2, 0, 6.1,
                          0, 0.2, 0, 3.1,
                          0, 0.2, 0, 8.1,
                          0, 0.2, 0, 4.1)),

                  (True, (0.1, 0.2, 0.1, 12.9,
                          0.1, 0.3, 0.1, 8.1,
                          0.1, 0.2, 0.3, 15.1,
                          0.15, 0.21, 0, 20.1,
                          0.5, 0.2, 0, 4.1,
                          0.5, 0.2, 0, 4.1,
                          0.3, 0.2, 0.1, 4.1,
                          0.4, 0.2, 0, 6.1,
                          0.2, 0.2, 0, 3.1,
                          0.8, 0.2, 0, 8.1,
                          0.9, 0.2, 0, 4.1)),

                  (True, (0.2, 0.2, 0.21, 12.3,
                          0.2, 0.2, 0.22, 8.2,
                          0.2, 0.2, 0.23, 15.2,
                          0.2, 0.2, 0.24, 20.2,
                          0.3, 0.2, 0.24, 4.1,
                          0.2, 0.2, 0.24, 4.1,
                          0.2, 0.23, 0.24, 4.1,
                          0.6, 0.2, 0.28, 6.1,
                          0.9, 1.2, 0.3, 3.1,
                          1.0, 0.2, 0.3, 8.1,
                          1.2, 0.2, 0.4, 4.1))
    ]
    
    def test_delay_controlled(self):
        
        for expected_result, delays in self.TEST_SUITE:
            
            mock_uri_opener = Mock()
            side_effect = generate_delays(delays)
            mock_uri_opener.send_mutant = MagicMock(side_effect=side_effect)
            delay_obj = ExactDelay('sleep(%s)')
            
            url = URL('http://moth/?id=1')
            req = FuzzableRequest(url)
            mutant = QSMutant(req)
            mutant.set_dc(url.querystring)
            mutant.set_token(('id', 0))
            
            ed = ExactDelayController(mutant, delay_obj, mock_uri_opener)
            controlled, responses = ed.delay_is_controlled()
            self.assertEqual(expected_result, controlled, delays)
    
    def test_delay_controlled_random(self):
        for expected_result, delays in self.TEST_SUITE:
            mock_uri_opener = Mock()
            side_effect = generate_delays(delays, rand_range=(0, 2))
            mock_uri_opener.send_mutant = MagicMock(side_effect=side_effect)
            delay_obj = ExactDelay('sleep(%s)')
            
            url = URL('http://moth/?id=1')
            req = FuzzableRequest(url)
            mutant = QSMutant(req)
            mutant.set_dc(url.querystring)
            mutant.set_token(('id', 0))
            
            ed = ExactDelayController(mutant, delay_obj, mock_uri_opener)
            controlled, responses = ed.delay_is_controlled()
            
            # This is where we change from test_delay_controlled, the basic
            # idea is that we'll allow false negatives but no false positives
            if expected_result:
                expected_result = [True, False]
            else:
                expected_result = [False]
                
            self.assertIn(controlled, expected_result, delays)
