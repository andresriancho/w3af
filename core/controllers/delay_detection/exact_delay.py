'''
exact_delay.py

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


class ExactDelay(object):
    '''
    Given that more than one vulnerability can be detected using time delays, just
    to name a couple blind SQL injections and OS commandings, I decided to create
    a generic class that will help me detect those vulnerabilities in an accurate
    and generic manner.

    This class works for EXACT time delays, this means that we control "exactly"
    how many seconds the remote server will "sleep" before returning the response.
    A good example to understand this is MySQL's sleep(x) vs. benchmark(...).
    '''

    DELTA = 0.5

    #
    #    Note that these delays are applied ONLY if all the previous delays worked
    #    so adding more here will only increase accurancy and not performance since
    #    you'll only get slower scans when there is a vulnerability, which is not
    #    the most common case
    #
    DELAY_SECONDS = [3, 1, 6, 1]

    def __init__(self, mutant, delay_obj, uri_opener):
        '''
        @param mutant: The mutant that will be sent (one or more times) to the
                       remote server in order to detect the time delay.

        @param delay_obj: A delay object as defined in delay.py file. Basically
                          an object that contains the string that would delay
                          the remote server (ie. sleep(%s) )
        '''
        self.mutant = mutant
        self.mutant.set_mod_value(self.mutant.get_original_value())

        self.delay_obj = delay_obj
        self.uri_opener = uri_opener

    def delay_is_controlled(self):
        '''
        All the logic/magic is in this method. The logic is very simple:
            * Try to delay the response in 4 seconds, if it works
            * Try to delay the response in 1 seconds, if it works
            * Try to delay the response in 6 seconds, if it works
              (note that these delays are actually determined by DELAY_SECONDS)
            * Then we have found a vulnerability!

        We go up and down and change the amount of seconds in order to make sure
        that WE are controlling the delay and there is no other external factor
        in place.
        '''
        responses = []
        
        #    Setup
        original_wait_time = self.get_original_time()

        for delay in self.DELAY_SECONDS:
            success, response = self.delay_for(delay, original_wait_time)
            if success:
                responses.append(response)
            else:
                return False, []

        return True, responses

    def delay_for(self, seconds, original_wait_time):
        '''
        Sends a request to the remote end that "should" delay the response in
        @param seconds.

        @param original_wait_time: The time that it takes to perform the
                                   request without adding any delays.

        @return: (True, response) if there was a delay. In order to make
                 things right we first send some requests to measure the
                 original wait time.
        '''
        delay_str = self.delay_obj.get_string_for_delay(seconds)
        mutant = self.mutant.copy()
        mutant.set_mod_value(delay_str)

        #    Send
        response = self.uri_opener.send_mutant(mutant, cache=False)

        #    Test
        delta = original_wait_time / 1.5
        if response.get_wait_time() > (original_wait_time + seconds - delta):
                return True, response

        return False, response

    def get_original_time(self, rep=3):
        original_wait_times = []

        for _ in xrange(rep):
            time = self.uri_opener.send_mutant(self.mutant,
                                               cache=False).get_wait_time()
            original_wait_times.append(time)
            
        return float(sum(original_wait_times)) / len(original_wait_times)
