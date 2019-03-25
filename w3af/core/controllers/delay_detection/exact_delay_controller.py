"""
exact_delay_controller.py

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
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.controllers.output_manager import out
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.core.data.url.helpers import new_no_content_resp


class ExactDelayController(object):
    """
    Given that more than one vulnerability can be detected using time delays,
    just to name a couple blind SQL injections and OS commandings, I decided to
    create a generic class that will help me detect those vulnerabilities in an
    accurate and generic manner.

    This class works for EXACT time delays, this means that we control "exactly"
    how many seconds the remote server will "sleep" before returning the
    response. A good example to understand this is MySQL's sleep(x) vs.
    benchmark(...).
    """

    # 25% more/less than the original wait time
    DELTA_PERCENT = 0.25

    #
    # Note that these delays are applied ONLY if all the previous delays worked
    # so adding more here will only increase accuracy and not performance since
    # you'll only get slower scans when there is a vulnerability, which is not
    # the most common case
    #
    DELAY_SECONDS = [8, 4, 9, 5, 14]

    def __init__(self, mutant, delay_obj, uri_opener):
        """
        :param mutant: The mutant that will be sent (one or more times) to the
                       remote server in order to detect the time delay.

        :param delay_obj: A delay object as defined in delay.py file. Basically
                          an object that contains the string that would delay
                          the remote server (ie. sleep(%s) )
        """
        if not isinstance(delay_obj, ExactDelay):
            raise TypeError('ExactDelayController requires ExactDelay as input')
        
        self.mutant = mutant
        self.mutant.set_token_value(mutant.get_token().get_original_value())

        self.delay_obj = delay_obj
        self.uri_opener = uri_opener
        self._debugging_id = None

    def set_debugging_id(self, debugging_id):
        self._debugging_id = debugging_id

    def get_debugging_id(self):
        return self._debugging_id

    def delay_is_controlled(self):
        """
        All the logic/magic is in this method. The logic is very simple:
            * Try to delay the response in 4 seconds, if it works
            * Try to delay the response in 1 seconds, if it works
            * Try to delay the response in 6 seconds, if it works
              (note that these delays are actually determined by DELAY_SECONDS)
            * Then we have found a vulnerability!

        We go up and down and change the amount of seconds in order to make sure
        that WE are controlling the delay and there is no other external factor
        in place.
        """
        responses = []

        for i, delay in enumerate(self.DELAY_SECONDS):

            # Added for the deserialization plugin
            assert delay < 100, 'Some ExactDelay instances can NOT handle large delays'

            # Only grep on the first test, to give the grep plugins the chance
            # to find something interesting. The other requests are not sent
            # to grep plugins for performance
            grep = i == 0

            # Please note that this call is cached, it will only generate HTTP
            # requests every N calls for the same HTTP request.
            original_rtt = self.uri_opener.get_average_rtt_for_mutant(mutant=self.mutant,
                                                                      debugging_id=self.get_debugging_id())

            # Try to introduce the delay
            success, response = self.delay_for(delay, original_rtt, grep)

            if not success:
                self._log_failure(delay, response)
                return False, []

            original_response = response
            #
            # The delay was successful, BUT... let's try one more thing to
            # reduce false positives: send the payload reversed, so if the
            # original payload was:
            #
            #       sleep(1)
            #
            # We now send:
            #
            #       )1(peels
            #
            # If we also receive success from the `delay_for` method, then
            # we're certain that it was because of a false positive.
            #
            # These false positives are usually generated by the server
            # being under heavy load and HTTP responses reaching us with
            # a lot of delay.
            #
            # Note that this approach might hide some real vulnerabilities
            # but the benefits are greater than the potential issues
            #
            success_on_reverse, response = self.delay_for(delay,
                                                          original_rtt,
                                                          False,
                                                          reverse=True)

            if success_on_reverse:
                self._log_failure_with_reverse(delay, response)
                return False, []

            # NOTE: log the original responses here, the reversed ones
            # don't make sense to show the report reader
            self._log_success(delay, original_response)
            responses.append(original_response)

        return True, responses

    def _log_success(self, delay, response):
        msg = (u'[did: %s] [id: %s] Successfully controlled HTTP response delay for'
               u' URL %s - parameter "%s" for %s seconds using %r, response'
               u' wait time was: %s seconds and response ID: %s.')
        self._log_generic(msg, delay, response)

    def _log_failure(self, delay, response):
        msg = (u'[did: %s] [id: %s] Failed to control HTTP response delay for'
               u' URL %s - parameter "%s" for %s seconds using %r, response'
               u' wait time was: %s seconds and response ID: %s.')
        self._log_generic(msg, delay, response)

    def _log_failure_with_reverse(self, delay, response):
        msg = (u'[did: %s] [id: %s] Successfully controlled the HTTP response'
               u' delay using the reverse payload, this is a false positive test'
               u' and should have failed. The previous delay was most likely'
               u' generated because of the server being under heavy load.'
               u' URL %s - parameter "%s" delayed for %s seconds using %r,'
               u' response wait time was: %s seconds and response ID: %s.')
        self._log_generic(msg, delay, response)

    def _log_generic(self, msg, delay, response):
        args = (self._debugging_id,
                id(self),
                self.mutant.get_url(),
                self.mutant.get_token_name(),
                delay,
                self.delay_obj,
                response.get_wait_time(),
                response.id)
        out.debug(msg % args)

    def delay_for(self, delay, original_wait_time, grep, reverse=False):
        """
        Sends a request to the remote end that "should" delay the response in
        `delay` seconds.

        :param delay: The delay object
        :param original_wait_time: The time that it takes to perform the
                                   request without adding any delays.
        :param grep: Should the framework grep the HTTP response sent for testing?
        :param reverse: Should we reverse the delay_str before sending it?

        :return: (True, response) if there was a delay. In order to make
                 things right we first send some requests to measure the
                 original wait time.
        """
        delay_str = self.delay_obj.get_string_for_delay(delay)
        delay_str = delay_str if not reverse else delay_str[::-1]

        mutant = self.mutant.copy()
        mutant.set_token_value(delay_str)

        # Set the upper and lower bounds
        delta = original_wait_time * self.DELTA_PERCENT

        # Upper bound is the highest number we'll wait for a response, it
        # doesn't mean that it is the highest delay that might happen on
        # the application.
        #
        # So, for example if the application logic (for some reason) runs
        # our payload three times, and we send:
        #
        #   sleep(10)
        #
        # The delay will be of 30 seconds, but we don't want to wait all
        # that time (using high timeouts for HTTP requests is *very* bad when
        # scanning slow apps).
        #
        # We just wait until `upper_bound` is reached
        upper_bound = original_wait_time + delta + delay * 2

        # The lower_bound is the lowest number of seconds we require for this
        # HTTP response to be considered "delayed".
        #
        # I tried with different variations of this, the first one included
        # original_wait_time and delta, but that failed in this scenario:
        #
        #   * RTT (which defines original_wait_time) is inaccurately high: 3 seconds
        #     instead of 1 second which was the expected result. This could be
        #     because of outliers in the measurement
        #
        #           https://github.com/andresriancho/w3af/issues/16902
        #
        #   * lower_bound is then set to original_wait_time - delta + delay
        #
        #   * The payload is sent and the response is delayed for 4 seconds
        #
        #   * The delay_for method yields false because of the bad RTT
        lower_bound = delay

        # Send, it is important to notice that we don't use the cache
        # to avoid any interference
        try:
            response = self.uri_opener.send_mutant(mutant,
                                                   grep=grep,
                                                   cache=False,
                                                   timeout=upper_bound,
                                                   debugging_id=self.get_debugging_id())
        except HTTPRequestException:
            #
            # We reach this part of the code when the server response times out
            #
            # Note that in the timeout parameter of send_mutant we're sending
            # the upper bound, so we reach this code if that upper bound is
            # exceeded. That can be because of:
            #
            #   * Network delays unrelated to our payload
            #
            #   * Our payload having an effect on the server, delaying the
            #     response so much that it triggers the timeout
            #
            args = (id(self), upper_bound, lower_bound, delay, upper_bound)
            msg = (u'[id: %s] HTTP response delay was %.2f.'
                   u' (lower, expected, upper): %.2f, %.2f, %.2f.')
            out.debug(msg % args)

            return True, new_no_content_resp(self.mutant.get_uri())

        # We reach this code when the HTTP timeout wasn't reached, but we might still
        # have a working delay. This is most of the cases I've seen.
        current_response_wait_time = response.get_wait_time()
        args = (id(self), current_response_wait_time, lower_bound, delay, upper_bound)
        msg = (u'[id: %s] HTTP response delay was %.2f.'
               u' (lower, expected, upper): %.2f, %.2f, %.2f.')
        out.debug(msg % args)

        if current_response_wait_time > lower_bound:
            return True, response

        return False, response
