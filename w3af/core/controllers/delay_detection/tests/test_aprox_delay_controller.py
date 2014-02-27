"""
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

"""
import unittest
import random

from mock import MagicMock, Mock

from w3af.core.controllers.delay_detection.aprox_delay_controller import AproxDelayController
from w3af.core.controllers.delay_detection.aprox_delay import AproxDelay
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest


def generate_delays(wanted_delays, rand_range=(0,0)):
    for delay_secs in wanted_delays:
        delay_secs += random.randint(*rand_range) / 10.0
        
        mock_response = Mock()
        mock_response.get_wait_time = Mock(return_value=delay_secs)
        
        yield mock_response
    
class TestAproxDelayController(unittest.TestCase):
    
    TEST_SUITE = [
                  # Basic, very easy to pass
                  #    The first three 0.1 are for getting the original delay
                  #
                  #    Then 0.13 and 0.5 are for showing that the second multiplier
                  #    does delay the response
                  #
                  #    Then we repeat the same thing 3 times for each
                  #    verification round
                  (True, (0.1, 0.1, 0.1, 0.13, 0.5) * 3),

                  # Setup phase changes
                  (True, (0.1, 0.2, 0.15, 0.13, 0.5) * 3),
                  (True, (0.1, 0.1, 0.1, 0.13, 0.3, 0.2, 0.2, 0.2, 0.23, 0.51, 0.2, 0.2, 0.1, 0.23, 0.59)),
                  
                  # Unexpected delay
                  (False, (0.1, 0.1, 0.1, 0.13, 0.3, 0.1, 0.1, 0.1, 0.75))
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
    
