'''
aprox_delay.py

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
from core.controllers.delay_detection.aprox_delay import AproxDelay
from core.controllers.delay_detection.delay_mixin import DelayMixIn


class AproxDelayController(DelayMixIn):
    '''
    Given that more than one vulnerability can be detected using time delays which
    are not 100% exact, just to name a couple: blind SQL injections using the
    MySQL's BENCHMARK and REDoS, I decided to create a generic class that will
    help me detect those vulnerabilities in an accurate and generic manner.

    This class works for approximated time delays, this means that we DO NOT
    NEED to control how many seconds the remote server will "sleep" before
    returning the response
    
    A good example to understand this is MySQL's sleep(x) vs. benchmark(...).
    This class solves the benchmark(...) issue while ExactDelay solves the
    sleep(x) issue.
    
    Note that these delays are applied ONLY if all the previous delays worked
    so adding more here will only increase accuracy and not performance since
    you'll only get slower scans when there is a vulnerability, which is not
    the most common case
    
    The delay multiplier means: "try to delay for twice the time of the
    original request". In other words, if the original request said
    BENCHMARK(2500000,MD5(1)) then if the multiplier is a 2 the next request
    will send BENCHMARK(5000000,MD5(1)) and if the multiplier is a 4 it will
    send BENCHMARK(10000000,MD5(1)).
    
    After sending the request, the algorithm will verify that the response
    was delayed at least multiplier * original_time to continue with the
    next step
    '''

    DELTA = 0.5

    DELAY_MULTIPLIER = [2, 4, 6, 8, 1, 2, 4]

    def __init__(self, mutant, delay_obj, uri_opener):
        '''
        @param mutant: The mutant that will be sent (one or more times) to the
                       remote server in order to detect the time delay.

        @param delay_obj: A delay object as defined in delay.py file. Basically
                          an object that contains the string that would delay
                          the remote server (ie. sleep(%s) )
        '''
        if not isinstance(delay_obj, AproxDelay):
            raise TypeError('ExactDelayController requires ExactDelay as input')

        self.mutant = mutant
        self.mutant.set_mod_value(self.mutant.get_original_value())

        self.delay_obj = delay_obj
        self.uri_opener = uri_opener

    def delay_is_controlled(self):
        '''
        All the logic/magic is in this method. The logic is very simple:
            * First send the payload as-is, and record the original time
            * Send the payload multiplied by 10, and record the time
            * If there's a big increase in the delay, start testing with the
              multipliers using this request as a base.
              
              If there's NO noticeable increase then multiply the payload by
              10 and try again. Try this 2 more times.
            * If the multipliers do their work, we have found a vulnerability!

        We go up and down and change the multiplier in order to make sure
        that WE are controlling the delay and there is no other external factor
        in place.
        '''
        responses = []
        
        #    Setup
        original_wait_time = self.get_original_time()
        
        for multiplier in [1, 10, 100, 500]:
            delays, resp = self.multiplier_delays_response(multiplier,
                                                           original_wait_time)
            if delays:
                break
        else:
            return False, []
        
        # This is the multiplier we know will add a delay to the remote end.
        # At this point we could report a vulnerability, but because we want to
        # reduce false positives, we perform the verification with the delay
        # multipliers
        base_multiplier = multiplier
        base_delay = resp.get_wait_time() - original_wait_time
        self.delay_obj.set_base_multiplier(multiplier)
        
        for multiplier in self.DELAY_MULTIPLIER:
            success, response = self.delay_controlled_by_mult(multiplier,
                                                              base_delay,
                                                              original_wait_time)
            if success:
                responses.append(response)
            else:
                return False, []

        return True, responses
    
    def multiplier_delays_response(self, multiplier, original_wait_time):
        '''
        @return: (True if the multiplier delays the response,
                  The HTTP response)
        '''
        delay_str = self.delay_obj.get_string_for_multiplier(multiplier)

        mutant = self.mutant.copy()
        mutant.set_mod_value(delay_str)

        #    Send
        response = self.uri_opener.send_mutant(mutant, cache=False)

        #    Test
        if response.get_wait_time() > (original_wait_time * 2):
                return True, response

        return False, response

    def delay_controlled_by_mult(self, multiplier, base_delay, original_wait_time):
        '''
        @return: (True if the multiplier delays the response when compared
                  with the base_delay,
                  The HTTP response)
        '''
        delay_str = self.delay_obj.get_string_for_multiplier(multiplier)

        mutant = self.mutant.copy()
        mutant.set_mod_value(delay_str)

        #    Send
        response = self.uri_opener.send_mutant(mutant, cache=False)

        #    Test
        delta = 0.3
        lower_limit = (original_wait_time + base_delay) * multiplier * (1 - delta)
        upper_limit = (original_wait_time + base_delay) * multiplier * (1 + delta)
        
        if lower_limit <= response.get_wait_time() <= upper_limit:
                return True, response

        return False, response

