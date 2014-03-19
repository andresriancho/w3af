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
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest


def generate_delays(wanted_delays, rand_range=(0, 0)):
    for delay_secs in wanted_delays:
        delay_secs += random.randint(*rand_range) / 10.0
        
        mock_response = Mock()
        mock_response.get_wait_time = Mock(return_value=delay_secs)
        
        yield mock_response


class TestExactDelay(unittest.TestCase):
    
    TEST_SUITE = [
                  # Basic, very easy to pass
                  # The three 0.1 are the calls to get_original_time
                  (True, (0.1, 0.1, 0.1, 3.5,
                          0.1, 0.1, 0.1, 2.1,
                          0.1, 0.1, 0.1, 6.1,
                          0.1, 0.1, 0.1, 2.2,
                          0.1, 0.1, 0.1, 3.4)),
                  
                  # Basic with a +0.1 delta
                  (True, (0.1, 0.1, 0.1, 3.1,
                          0.1, 0.1, 0.1, 2.1,
                          0.1, 0.1, 0.1, 6.1,
                          0.1, 0.1, 0.1, 2.1,
                          0.1, 0.1, 0.1, 3.1)),
                  
                  # Basic without controlled delays
                  (False, [0.1] * 20),

                  # Basic with server under heavy load after setup
                  (False, (0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5,
                           0, 0, 0, 5)),

                  # Basic with server under random heavy load after setup
                  (False, (0, 0, 0, 5,
                           0, 0, 0, 2,
                           0, 0, 0, 2,
                           0, 0, 0, 5,
                           0, 0, 0, 7)),

                  # Basic with server under random heavy load after setup
                  (False, (0.1, 0.2, 0.2, 5,
                           0.1, 0.2, 0.2, 2,
                           0.1, 0.2, 0.2, 2,
                           0.1, 0.2, 0.2, 2,
                           0.1, 0.2, 0.2, 2)),

                  # Basic with server under random heavy load after setup
                  (False, (0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7,
                           0.1, 0.2, 0.2, 7)),
                  
                  # With various delays in the setup phase
                  (True, (0, 0.2, 0, 3.1,
                          0, 0.1, 0.15, 2.1,
                          0, 0.2, 0, 6.1,
                          0, 0.2, 0, 2.1,
                          0, 0.2, 0.1, 3.1)),

                  (True, (0.1, 0.2, 0.1, 3.1,
                          0.1, 0.2, 0.1, 2.1,
                          0.1, 0.2, 0.1, 6.1,
                          0.1, 0.2, 0.1, 2.1,
                          0.1, 0.2, 0.1, 3.1)),

                  (True, (0.2, 0.2, 0.21, 3.2,
                          0.2, 0.2, 0.22, 2.2,
                          0.2, 0.2, 0.23, 6.2,
                          0.2, 0.2, 0.24, 2.2,
                          0.2, 0.2, 0.25, 3.2)),]
    
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
            mutant.set_var('id', 0)
            
            ed = ExactDelayController(mutant, delay_obj, mock_uri_opener)
            controlled, responses = ed.delay_is_controlled()
            self.assertEqual(expected_result, controlled, delays)
    
    def test_delay_controlled_random(self):
        for expected_result, delays in self.TEST_SUITE:
            print delays
            mock_uri_opener = Mock()
            side_effect = generate_delays(delays, rand_range=(0,2))
            mock_uri_opener.send_mutant = MagicMock(side_effect=side_effect)
            delay_obj = ExactDelay('sleep(%s)')
            
            url = URL('http://moth/?id=1')
            req = FuzzableRequest(url)
            mutant = QSMutant(req)
            mutant.set_dc(url.querystring)
            mutant.set_var('id', 0)
            
            ed = ExactDelayController(mutant, delay_obj, mock_uri_opener)
            controlled, responses = ed.delay_is_controlled()
            
            # This is where we change from test_delay_controlled, the basic
            # idea is that we'll allow false negatives but no false positives
            if expected_result == True:
                expected_result = [True, False]
            else:
                expected_result = [False,]
                
            self.assertIn(controlled, expected_result, delays)
