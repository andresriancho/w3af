"""
aprox_delay_controller.py

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
from w3af.core.controllers.delay_detection.aprox_delay import AproxDelay

LINEARLY = 1
EXPONENTIALLY = 2


class AproxDelayController(object):
    """
    Given that more than one vulnerability can be detected using time delays
    which are not 100% exact, just to name a couple: blind SQL injections using
    the MySQL's BENCHMARK and REDoS, I decided to create a generic class that
    will help me detect those vulnerabilities in an accurate and generic manner.

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
    """
    DELAY_DIFF_MULT = 4.0

    DELAY_SETTINGS = {LINEARLY: [1, 10, 100, 500],
                      EXPONENTIALLY: [1, 2, 3, 4, 5, 6, 7, 8]}

    def __init__(self, mutant, delay_obj, uri_opener, delay_setting=LINEARLY):
        """
        :param mutant: The mutant that will be sent (one or more times) to the
                       remote server in order to detect the time delay.

        :param delay_obj: A delay object as defined in delay.py file. Basically
                          an object that contains the string that would delay
                          the remote server (ie. sleep(%s) )
        """
        if not isinstance(delay_obj, AproxDelay):
            raise TypeError('ExactDelayController requires ExactDelay as input')
        
        if delay_setting not in (LINEARLY, EXPONENTIALLY):
            raise TypeError('delay_increases needs to be one of LINEARLY'
                            ' or EXPONENTIALLY')

        self.mutant = mutant
        self.mutant.set_token_value(mutant.get_token().get_original_value())

        self.delay_obj = delay_obj
        self.uri_opener = uri_opener
        self.delay_setting = delay_setting
        self._debugging_id = None

    def set_debugging_id(self, debugging_id):
        self._debugging_id = debugging_id

    def get_debugging_id(self):
        return self._debugging_id

    def delay_is_controlled(self):
        """
        All the logic/magic is in this method. The logic is very simple:

            * First send the payload as-is, and record the original time

            * Send the payload multiplied by DELAY_SETTINGS, and record
              the time. If there's a big increase in the delay then we've
              found a vulnerability!

            * Increase the multiplier if no delay is found.

        Note that we don't start directly with the highest multiplier because
        these aprox delays are usually related with CPU bound functions (not
        sleep). If we start with the highest maybe we could break something.
        """
        responses = []

        original_rtt = self.uri_opener.get_average_rtt_for_mutant(mutant=self.mutant,
                                                                  debugging_id=self.get_debugging_id())

        # Find a multiplier that delays
        multiplier = self.find_delay_multiplier(original_rtt, responses)
        if multiplier is None:
            return False, responses

        # We want to make sure that the multiplier actually works and
        # that the delay is stable
        for _ in xrange(3):
            original_rtt = self.uri_opener.get_average_rtt_for_mutant(mutant=self.mutant,
                                                                      debugging_id=self.get_debugging_id())
            delays, resp = self.multiplier_delays_response(multiplier,
                                                           original_rtt,
                                                           grep=False)
            responses.append(resp)

            if not delays:
                break
        else:
            # All the delays were confirmed, vuln!
            return True, responses

        return False, responses
    
    def find_delay_multiplier(self, original_rtt, responses):
        for i, multiplier in enumerate(self.DELAY_SETTINGS[self.delay_setting]):
            # Only grep the first response, this way we let the grep plugins find stuff
            # but afterwards we get a performance improvement
            grep = i == 0

            delays, resp = self.multiplier_delays_response(multiplier, original_rtt, grep)
            responses.append(resp)
            if delays:
                return multiplier
        
        # No multiplier was able to make an impact in the delay
        return None
    
    def multiplier_delays_response(self, multiplier, original_rtt, grep):
        """
        :return: (True if the multiplier delays the response,
                  The HTTP response)
        """
        delay_str = self.delay_obj.get_string_for_multiplier(multiplier)

        mutant = self.mutant.copy()
        mutant.set_token_value(delay_str)

        # Send
        response = self.uri_opener.send_mutant(mutant,
                                               cache=False,
                                               grep=grep)

        # Test
        if response.get_wait_time() > (original_rtt * self.DELAY_DIFF_MULT):
                return True, response

        return False, response
