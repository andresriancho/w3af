'''
test_aprox_delay_controller.py

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

'''
import unittest
import random

from mock import MagicMock, Mock

from core.controllers.delay_detection.aprox_delay_controller import AproxDelayController
from core.controllers.delay_detection.aprox_delay import AproxDelay
from core.data.fuzzer.mutants.querystring_mutant import QSMutant
from core.data.parsers.url import URL
from core.data.request.fuzzable_request import FuzzableRequest


def generate_delays(wanted_delays, rand_range=(0,0)):
    for delay_secs in wanted_delays:
        delay_secs += random.randint(*rand_range) / 10.0
        
        mock_response = Mock()
        mock_response.get_wait_time = Mock(return_value=delay_secs)
        
        yield mock_response
    
class TestAproxDelayController(unittest.TestCase):
    
    # DELAY_MULTIPLIER = [2, 4, 6, 8, 1, 2, 4]
    
    TEST_SUITE = [
                  # Basic, very easy to pass
                  #    The first three 0.1 are for getting the original delay
                  #    Then 0.13 and 0.5 are for showing that the delay works
                  #    Finally the other numbers are (0.5 * MULT) + 0.1
                  (True, (0.1, 0.1, 0.1, 0.13, 0.5, 1.1, 2.1, 3.1, 4.1, 0.6, 1.1, 2.1)),

                  # One more step to verify initial delay
                  #    The first three 0.1 are for getting the original delay
                  #    Then 0.13 and 0.5 are for showing that the delay works
                  #    Finally the other numbers are (0.5 * MULT) + 0.1
                  (True, (0.1, 0.1, 0.1, 0.13, 0.19, 0.49, 1.1, 2.1, 3.1, 4.1, 0.6, 1.1, 2.1)),
                  
                  # First multiplier does NOT multiply delay 
                  (False, (0.1, 0.1, 0.1, 0.13, 0.5, 0.6, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1)),

                  # Third multiplier does NOT multiply delay 
                  (False, (0.1, 0.1, 0.1, 0.13, 0.5, 1.1, 2.1, 0.1, 0.1, 0.1, 0.1, 0.1)),

                  # Fifth multiplier does NOT multiply delay by one
                  # Server under high load, we do not control the delay 
                  (False, (0.1, 0.1, 0.1, 0.13, 0.5, 1.1, 2.1, 3.1, 4.1, 3.6, 4.1, 3.1)),

                  # There is no need to check anything since the initial
                  # tests with [1, 10, 100, 500] fail
                  (False, (0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1)),

                  ]
    
    def test_delay_controlled(self):
        
        for expected_result, delays in self.TEST_SUITE:

            mock_uri_opener = Mock()
            side_effect = generate_delays(delays)
            mock_uri_opener.send_mutant = MagicMock(side_effect=side_effect)
            delay_obj = AproxDelay('%s9!', '1', 10)
            
            url = URL('http://moth/?id=1')
            req = FuzzableRequest(url)
            mutant = QSMutant(req)
            mutant.set_dc(url.querystring)
            mutant.set_var('id', 0)
            
            ed = AproxDelayController(mutant, delay_obj, mock_uri_opener)
            controlled, responses = ed.delay_is_controlled()
            self.assertEqual(expected_result, controlled, delays)
    
    def test_delay_controlled_random(self):
        for expected_result, delays in self.TEST_SUITE:
            
            mock_uri_opener = Mock()
            side_effect = generate_delays(delays, rand_range=(0,2))
            mock_uri_opener.send_mutant = MagicMock(side_effect=side_effect)
            delay_obj = AproxDelay('%s9!', '1', 10)
            
            url = URL('http://moth/?id=1')
            req = FuzzableRequest(url)
            mutant = QSMutant(req)
            mutant.set_dc(url.querystring)
            mutant.set_var('id', 0)
            
            adc = AproxDelayController(mutant, delay_obj, mock_uri_opener)
            controlled, responses = adc.delay_is_controlled()
            
            # This is where we change from test_delay_controlled, the basic
            # idea is that we'll allow false negatives but no false positives
            if expected_result == True:
                expected_result = [True, False]
            else:
                expected_result = [False,]
                
            self.assertIn(controlled, expected_result, delays)