"""
extended_urllib.py

Copyright 2006 Andres Riancho

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
import time
import uuid
import urllib
import socket
import OpenSSL
import urllib2
import httplib
import threading
import traceback
import functools

from contextlib import contextmanager
from collections import deque
from httplib import BadStatusLine

# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf
import opener_settings

from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              ConnectionPoolException,
                                              HTTPRequestException,
                                              ScanMustStopByUnknownReasonExc,
                                              ScanMustStopByKnownReasonExc,
                                              ScanMustStopByUserRequest)
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.parsers.doc.http_request_parser import http_request_parser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.handlers.keepalive import URLTimeoutError
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.dc.headers import Headers
from w3af.core.data.user_agent.random_user_agent import get_random_user_agent
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.url.helpers import get_clean_body, get_exception_reason
from w3af.core.data.url.response_meta import ResponseMeta, SUCCESS
from w3af.core.data.url.get_average_rtt import GetAverageRTTForMutant
from w3af.core.data.url.constants import (MAX_ERROR_COUNT,
                                          MAX_RESPONSE_COLLECT,
                                          SOCKET_ERROR_DELAY,
                                          TIMEOUT_MULT_CONST,
                                          TIMEOUT_ADJUST_LIMIT,
                                          DEFAULT_TIMEOUT,
                                          ACCEPTABLE_ERROR_RATE,
                                          ERROR_DELAY_LIMIT,
                                          MAX_TIMEOUT,
                                          MIN_TIMEOUT,
                                          TIMEOUT_INCREASE_MULT,
                                          TIMEOUT_UPDATE_ELAPSED_MIN)


class ExtendedUrllib(object):
    """
    This is a urllib2 wrapper.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        self.settings = opener_settings.OpenerSettings()
        self._opener = None
        self._w3af_core = None
        self._average_rtt_mutant = GetAverageRTTForMutant(self)

        # In exploit mode we disable some timeout/delay/error handling stuff
        self.exploit_mode = False

        # For error handling, the first "last response" is set to SUCCESS to
        # allow the _should_stop_scan method to match it's "SFFFF...FFF" pattern
        self._last_responses = deque(maxlen=MAX_RESPONSE_COLLECT)
        self._last_responses.extend([ResponseMeta(True, SUCCESS)] * 100)
        self._count_lock = threading.RLock()

        # For rate limiting and timeouts
        self._rate_limit_last_time_called = 0.0
        self._rate_limit_lock = threading.RLock()
        self._adjust_timeout_lock = threading.RLock()
        self._adjust_timeout_last_call = 0.0

        # Keep track of sum(rtt) for each debugging_id
        self._rtt_sum_debugging_id = SynchronizedLRUDict(capacity=128)

        # Avoid multiple consecutive calls to reduce the worker pool size
        self._last_call_to_adjust_workers = None
        self._should_adjust_workers_lock = threading.RLock()

        # For timeout auto adjust and general stats
        self._total_requests = 0

        # Timeout is kept by host
        self._host_timeout = {}
        self._global_timeout = DEFAULT_TIMEOUT

        # Used in the pause on HTTP error feature to keep track of when the
        # core slept waiting for the remote end to be reachable
        self._sleep_log = {}
        self._clear_sleep_log()

        # User configured options (in an indirect way)
        self._grep_queue_put = None
        self._evasion_plugins = []
        self._user_paused = False
        self._user_stopped = False
        self._stop_exception = None

    def get_average_rtt_for_mutant(self, *args, **kwargs):
        return self._average_rtt_mutant.get_average_rtt_for_mutant(*args, **kwargs)

    def pause(self, pause_yes_no):
        """
        When the core wants to pause a scan, it calls this method, in order to
        freeze all actions

        :param pause_yes_no: True if I want to pause the scan;
                             False to un-pause it.
        """
        self._user_paused = pause_yes_no

    def stop(self):
        """
        Called when the user wants to finish a scan.
        """
        self._user_stopped = True

    def set_w3af_core(self, w3af_core):
        self._w3af_core = w3af_core

    def get_w3af_core(self):
        return self._w3af_core

    def has_w3af_core(self):
        return self._w3af_core is not None

    def _before_send_hook(self, request):
        """
        This is a method that is called before every request is sent. I'm using
        it as a hook implement:
            - The pause/stop feature
            - Memory debugging features
        """
        # Handle errors (HTTP timeout, etc.)
        self._raise_if_should_stop()

        self._pause_and_stop()
        self._pause_on_http_error(request)

        if not self.exploit_mode:
            self._rate_limit()
            self._auto_adjust_timeout(request)

        # Increase the request count
        self._total_requests += 1

        # If the request has no debugging_id, then we add one here
        # this is useful for tracking any errors and retries generated by
        # the request
        if request.debugging_id is None:
            request.debugging_id = rand_alnum(8)

    def set_exploit_mode(self, exploit_mode):
        self.exploit_mode = exploit_mode

        # Set the timeout to DEFAULT_TIMEOUT
        self.clear_timeout()

        # Closes all HTTPConnections so all new requests are sent using the
        # DEFAULT_TIMEOUT
        self.settings.close_connections()

    def set_timeout(self, timeout, host):
        """
        Sets the timeout to use in HTTP requests, usually called by the auto
        timeout adjust feature in extended_urllib.py
        """
        # Set the min and max limits
        timeout = min(MAX_TIMEOUT, timeout)
        timeout = max(MIN_TIMEOUT, timeout)

        msg = 'Updating socket timeout for %s from %.2f to %.2f seconds'
        om.out.debug(msg % (host, self.get_timeout(host), timeout))

        self._host_timeout[host] = timeout

    def get_timeout(self, host):
        """
        :return: The timeout to use in HTTP requests, will be equal to the user
                 configured setting if the auto timeout adjust feature is
                 disabled, but when enabled this value will change during the
                 scan.
        """
        return self._host_timeout.get(host, self._global_timeout)

    def clear_timeout(self):
        """
        Called when the scan has finished/this opener settings won't be used
        anymore.

        :return: None
        """
        self._host_timeout = {}
        configured_timeout = self.settings.get_configured_timeout()

        if configured_timeout != 0:
            self._global_timeout = configured_timeout
        else:
            # Get ready for the next scan, which we don't want to be affected
            # by the timeout set in the previous scan
            self._global_timeout = DEFAULT_TIMEOUT

    def _auto_adjust_timeout(self, request):
        """
        By default the timeout value at OpenerSettings is set to 0, which means
        that w3af needs to auto-adjust it based on the HTTP request/response
        RTT. This method takes care of the process of adjusting the socket
        timeout.

        The objective of auto-adjusting the timeout is to "fail fast" on
        requests which are going to fail anyways. In previous versions of w3af
        the default timeout was 15 seconds, which made the scanner delay A LOT
        on URLs which (for some reason like heavy processing on the server side)
        failed anyways.

        We calculate and adjust the new timeout every 50 successful requests.

        The timeout is calculated using average(RTT) * TIMEOUT_MULT_CONST , then
        for example if the average RTT is 0.3 seconds and the TIMEOUT_MULT_CONST
        is at 6.5 we end up with a real socket timeout of 1.95

        The TIMEOUT_MULT_CONST might be lowered by advanced users to achieve
        faster scans in scenarios where timeouts are slowing down the scans.

        :see: https://github.com/andresriancho/w3af/issues/8698
        :return: None, we adjust the value at the "settings" attribute
        """
        with self._adjust_timeout_lock:
            if not self._should_auto_adjust_timeout_now():
                return

        host = request.get_domain()
        average_rtt, num_samples = self.get_average_rtt(TIMEOUT_ADJUST_LIMIT,
                                                        host)

        if num_samples < (TIMEOUT_ADJUST_LIMIT / 2):
            msg = ('Not enough samples collected (%s) to adjust timeout.'
                   ' Keeping the current value of %s seconds')
            om.out.debug(msg % (num_samples, self.get_timeout(host)))
        else:
            timeout = average_rtt * TIMEOUT_MULT_CONST
            self.set_timeout(timeout, host)

    def _increase_timeout_on_error(self, request, exception):
        """
        We get here when the framework found an error like connection reset,
        socket timeout, etc.

        If we got a connection reset / timeout error, then we know that we
        have to "slow down". The remote server might be having high loads,
        the network could be busy, etc.

        We just increase the timeout to give the next connections / requests
        more time to wait for the response.

        :param request: The HTTP request that triggered the error
        :param exception: The original exception that lead us here
        :return: None
        """
        # Get current timeout
        host = request.get_domain()
        timeout = self.get_timeout(host)

        # We increase it without a limit because the limit is set in set_timeout
        timeout *= TIMEOUT_INCREASE_MULT

        msg = 'Will increase timeout to %.2f seconds after HTTP socket error (did:%s)'
        args = (timeout, request.debugging_id)
        om.out.debug(msg % args)

        # Set new timeout
        self.set_timeout(timeout, host)

    def get_average_rtt(self, count=TIMEOUT_ADJUST_LIMIT, host=None):
        """
        :param count: The number of HTTP requests to sample the RTT from
        :param host: If specified filter the requests by host before calculating
                     the average RTT
        :return: Tuple with (average RTT from the last `count` requests,
                             the number of successful responses, which contain
                             an RTT, and were used to calculate the average RTT)
        """
        rtt_sum = 0.0
        add_count = 0
        last_n_responses = list(self._last_responses)[-count:]

        for response_meta in last_n_responses:
            if host is not None:
                if response_meta.host != host:
                    continue

            if response_meta.rtt is not None:
                rtt_sum += response_meta.rtt
                add_count += 1

        if not add_count:
            return None, 0
        else:
            average_rtt = float(rtt_sum) / add_count
            return average_rtt, add_count

    def _should_auto_adjust_timeout_now(self):
        """
        :return: True if we need to auto adjust the timeout now
        """
        if self.settings.get_configured_timeout() != 0:
            # The user disabled the timeout auto-adjust feature
            return False

        if self.get_total_requests() == 0:
            return False

        if self.get_total_requests() % TIMEOUT_ADJUST_LIMIT != 0:
            return False

        elapsed = time.time() - self._adjust_timeout_last_call
        if elapsed < TIMEOUT_UPDATE_ELAPSED_MIN:
            return False

        self._adjust_timeout_last_call = time.time()
        return True

    def get_total_requests(self):
        """
        :return: The number of requests sent (successful, timeout, failed, all
                 are counted here).
        """
        return self._total_requests

    def _pause_on_http_error(self, request):
        """
        This method will pause all scan threads for an increasing period of time
        based on the HTTP error rate. HTTP errors are timeouts, network
        unreachable, etc. things like 404, 403, 500 are NOT considered errors.

        The objective of this method is to give the remote server, or local
        connection, the chance to recover from their errors without killing the
        w3af scan.

        When the error rate is lower than 5% nothing is done. We accept some
        errors.

        If error rate is higher we delay the threads for some time, give the
        remote server/local connection time to recover, and then continue with
        the scan as usual.

        The error rate is multiplied by SOCKET_ERROR_DELAY to get the real delay
        time in seconds.

        The error rate starts at zero, so no delay is added at the beginning

        :return: None, but might delay the requests which go out to the network
        :see: https://github.com/andresriancho/w3af/issues/4811
        :see: https://github.com/andresriancho/w3af/issues/8852
        """
        with self._rate_limit_lock:

            error_rate = self.get_error_rate()
            if not self._should_pause_on_http_error(error_rate):
                return

            pending_pause, lower_error_rate = self._has_pending_pause(error_rate)
            if not pending_pause:
                return

            # Logging
            error_sleep = SOCKET_ERROR_DELAY * error_rate
            msg = ('Sleeping for %s seconds before sending HTTP request to'
                   ' "%s" (did:%s) after receiving URL/socket error. The ExtendedUrllib'
                   ' error rate is at %s%%')
            args = (error_sleep, request.url_object, request.debugging_id, error_rate)
            om.out.debug(msg % args)

            # The actual delay
            time.sleep(error_sleep)

            # Record this delay
            self._sleep_log[lower_error_rate] = True

            # Clear if needed
            if self.get_total_requests() % 100 == 0:
                self._clear_sleep_log()

    def _clear_sleep_log(self):
        self._sleep_log = {}

        step = ACCEPTABLE_ERROR_RATE * 2
        data = [(i, False) for i in xrange(0, 110, step)]

        self._sleep_log.update(data)

    def _has_pending_pause(self, error_rate):
        """
        :param error_rate: The current error rate
        :return: (False if we don't need to sleep/delay,
                  The rounded error rate used to query the sleep log)
        """
        step = ACCEPTABLE_ERROR_RATE * 2
        lower_error_rate = divmod(error_rate, step)[0] * step
        return not self._sleep_log[lower_error_rate], lower_error_rate

    def _should_pause_on_http_error(self, error_rate):
        """
        :param error_rate: The current error rate
        :return: True if we should analyze enter the pause on error
        """
        if error_rate <= ACCEPTABLE_ERROR_RATE:
            return False

        if self.get_total_requests() % ERROR_DELAY_LIMIT == 0:
            return True

        return False

    def _rate_limit(self):
        """
        Makes sure that we don't send more than X HTTP requests per seconds
        :return:
        """
        max_requests_per_second = self.settings.get_max_requests_per_second()

        if max_requests_per_second <= 0:
            return

        min_interval = 1.0 / float(max_requests_per_second)
        elapsed = time.clock() - self._rate_limit_last_time_called
        left_to_wait = min_interval - elapsed

        with self._rate_limit_lock:
            if left_to_wait > 0:
                #
                # This is useful for debugging, but will fill the output log in most
                # scenarios, you have been warned
                #
                #om.out.debug('ExtendedUrllib rate limit in place. Blocking all HTTP'
                #             ' requests for %s seconds.' % left_to_wait)
                time.sleep(left_to_wait)

        self._rate_limit_last_time_called = time.clock()

    def _raise_if_should_stop(self):
        # There might be errors that make us stop the process, the exception
        # was already raised (see below) but we want to make sure that we
        # keep raising it until the w3afCore really stops.
        if self._stop_exception is not None:
            # pylint: disable=E0702
            raise self._stop_exception
            # pylint: enable=E0702

    def _pause_and_stop(self):
        """
        This method sleeps until self._user_paused is False.
        """
        def analyze_state():
            # This handles the case where the user pauses and then stops
            if self._user_stopped:
                # Raise the exception to stop the scan, this exception will be
                # raised all the time until we un-set the self._user_stopped
                # attribute
                msg = 'The user stopped the scan.'
                raise ScanMustStopByUserRequest(msg)

            # Handle errors (HTTP timeout, etc.)
            self._raise_if_should_stop()

        while self._user_paused:
            time.sleep(0.2)
            analyze_state()

        analyze_state()

    def clear(self):
        """
        Clear all status set during the scanner run
        """
        self._user_stopped = False
        self._user_paused = False
        self._stop_exception = None
        self._total_requests = 0
        self.set_exploit_mode(False)
        self._last_responses.extend([ResponseMeta(True, SUCCESS)] * 100)

    def end(self):
        """
        This method is called when the ExtendedUrllib is not going to be used
        anymore.
        """
        self._opener = None

        self.clear()
        self.clear_timeout()

        self.settings.clear_cookies()
        self.settings.clear_cache()
        self.settings.close_connections()

    def restart(self):
        self.end()

    def setup(self):
        if self.settings.need_update or self._opener is None:
            self.settings.need_update = False
            self.settings.build_openers()
            self._opener = self.settings.get_custom_opener()

            self.clear_timeout()

    def get_headers(self, uri):
        """
        :param uri: The URI we want to know the request headers

        :return: A Headers object with the HTTP headers that would be added by
                the library when sending a request to uri.
        """
        req = HTTPRequest(uri)
        req = self.add_headers(req)
        return Headers(req.headers)

    def get_cookies(self):
        """
        :return: The cookies that this uri opener has collected during this scan
        """
        return self.settings.get_cookies()

    def get_new_session(self):
        return str(uuid.uuid4())

    def send_clean(self, mutant, debugging_id=None, grep=True):
        """
        Sends a mutant to the network (without using the cache) and then returns
        the HTTP response object and a sanitized response body (which doesn't
        contain any traces of the injected payload).

        The sanitized version is useful for having clean comparisons between two
        responses that were generated with different mutants.

        :param mutant: The mutant to send to the network.
        :param debugging_id: A unique identifier for this call to audit()
        :return: (HTTP response, Sanitized HTTP response body)
        """
        http_response = self.send_mutant(mutant,
                                         cache=False,
                                         debugging_id=debugging_id,
                                         grep=grep)
        clean_body = get_clean_body(mutant, http_response)

        return http_response, clean_body

    def send_raw_request(self, head, postdata, fix_content_len=True):
        """
        In some cases the ExtendedUrllib user wants to send a request that was
        typed in a textbox or is stored in a file. When something like that
        happens, this library allows the user to send the request by specifying
        two parameters for the send_raw_request method:

        :param head: "<method> <URI> <HTTP version>\r\nHeader: Value\r\n..."
        :param postdata: The data as string
                         If set to '' or None, no postdata is sent
        :param fix_content_len: Indicates if the content length has to be fixed

        :return: An HTTPResponse object.
        """
        # Parse the two strings
        fuzz_req = http_request_parser(head, postdata)

        # Fix the content length
        if fix_content_len:
            headers = fuzz_req.get_headers()
            fixed = False
            for h in headers:
                if h.lower() == 'content-length':
                    headers[h] = str(len(postdata))
                    fixed = True
            if not fixed and postdata:
                headers['content-length'] = str(len(postdata))
            fuzz_req.set_headers(headers)

        # Send it
        function_reference = getattr(self, fuzz_req.get_method())
        return function_reference(fuzz_req.get_uri(), data=fuzz_req.get_data(),
                                  headers=fuzz_req.get_headers(), cache=False,
                                  grep=False)

    def send_mutant(self, mutant, callback=None, grep=True, cache=True,
                    cookies=True, session=None,
                    error_handling=True, timeout=None,
                    follow_redirects=False, use_basic_auth=True,
                    respect_size_limit=True,
                    debugging_id=None,
                    binary_response=False):
        """
        Sends a mutant to the remote web server.

        :param callback: If None, return the HTTP response object, else call
                         the callback with the mutant and the http response as
                         parameters.

        :param debugging_id: A unique identifier for this call to audit()

        :return: The HTTPResponse object associated with the request
                 that was just sent.
        """
        #
        # IMPORTANT NOTE: If you touch something here, the whole framework may
        # stop working!
        #
        uri = mutant.get_uri()
        data = mutant.get_data()
        headers = mutant.get_all_headers()

        # Also add the cookie header; this is needed by the CookieMutant
        if cookies:
            mutant_cookie = mutant.get_cookie()
            if mutant_cookie:
                headers['Cookie'] = str(mutant_cookie)

        args = (uri,)
        kwargs = {
            'data': data,
            'headers': headers,
            'grep': grep,
            'cache': cache,
            'cookies': cookies,
            'session': session,
            'error_handling': error_handling,
            'timeout': timeout,
            'follow_redirects': follow_redirects,
            'use_basic_auth': use_basic_auth,
            'respect_size_limit': respect_size_limit,
            'debugging_id': debugging_id,
            'binary_response': binary_response
        }
        method = mutant.get_method()

        functor = getattr(self, method)
        res = functor(*args, **kwargs)

        if callback is not None:
            # The user specified a custom callback for analyzing the HTTP
            # response this is commonly used when sending requests in an
            # async way.
            callback(mutant, res)

        return res

    def GET(self, uri, data=None, headers=Headers(), cache=False,
            grep=True, cookies=True, session=None,
            respect_size_limit=True, new_connection=False,
            error_handling=True, timeout=None, follow_redirects=False,
            use_basic_auth=True, use_proxy=True, debugging_id=None,
            binary_response=False):
        """
        HTTP GET a URI using a proxy, user agent, and other settings
        that where previously set in opener_settings.py .

        :param uri: This is the URI to GET, with the query string included.
        :param data: Object to send as post-data, usually a string or a data
                     container
        :param headers: Any special headers that will be sent with this request
        :param cache: Should the library search the local cache for a response
                      before sending it to the wire?
        :param grep: Should grep plugins be applied to this request/response?
        :param timeout: If None we'll use the configured (opener settings)
                        timeout or the auto-adjusted value. Otherwise we'll use
                        the defined timeout as the socket timeout value for this
                        request. The timeout is specified in seconds
        :param cookies: Send stored cookies in request (or not)
        :param session: The browser session / cookiejar to use in this request
        :param follow_redirects: Follow 30x redirects (or not)
        :param debugging_id: A unique identifier for this call to audit()

        :return: An HTTPResponse object.
        """
        if not isinstance(uri, URL):
            raise TypeError('The uri parameter of ExtendedUrllib.GET() must be'
                            ' of url.URL type.')

        if not isinstance(headers, Headers):
            raise TypeError('The header parameter of ExtendedUrllib.GET() must'
                            ' be of Headers type.')

        # Validate what I'm sending, init the library (if needed)
        self.setup()

        host = uri.get_domain()
        timeout = self.get_timeout(host) if timeout is None else timeout

        req = HTTPRequest(uri, cookies=cookies, session=session,
                          cache=cache, data=data,
                          error_handling=error_handling, method='GET',
                          retries=self.settings.get_max_retrys(),
                          timeout=timeout, new_connection=new_connection,
                          follow_redirects=follow_redirects,
                          use_basic_auth=use_basic_auth, use_proxy=use_proxy,
                          debugging_id=debugging_id,
                          binary_response=binary_response)
        req = self.add_headers(req, headers)

        with raise_size_limit(respect_size_limit):
            return self.send(req, grep=grep)

    def POST(self, uri, data='', headers=Headers(), grep=True, cache=False,
             cookies=True, session=None, error_handling=True, timeout=None,
             follow_redirects=None, use_basic_auth=True, use_proxy=True,
             debugging_id=None, new_connection=False,
             respect_size_limit=None,
             binary_response=False):
        """
        POST's data to a uri using a proxy, user agents, and other settings
        that where set previously.

        :param uri: This is the url where to post.
        :param data: A string with the data for the POST.
        :param debugging_id: A unique identifier for this call to audit()

        :see: The GET() for documentation on the other parameters
        :return: An HTTPResponse object.
        """
        if not isinstance(uri, URL):
            raise TypeError('The uri parameter of ExtendedUrllib.POST() must'
                            ' be of url.URL type. Got %s instead.' % type(uri))

        if not isinstance(headers, Headers):
            raise TypeError('The header parameter of ExtendedUrllib.POST() must'
                            ' be of Headers type.')

        #    Validate what I'm sending, init the library (if needed)
        self.setup()

        # follow_redirects is ignored because according to the RFC browsers
        # should not follow 30x redirects on POST

        #
        #    Create and send the request
        #
        #    Please note that the cache=False overrides the user setting
        #    since we *never* want to return cached responses for POST
        #    requests.
        #
        data = str(data)
        host = uri.get_domain()
        timeout = self.get_timeout(host) if timeout is None else timeout

        req = HTTPRequest(uri, data=data, cookies=cookies, session=session,
                          cache=False, error_handling=error_handling, method='POST',
                          retries=self.settings.get_max_retrys(),
                          timeout=timeout, new_connection=new_connection,
                          use_basic_auth=use_basic_auth, use_proxy=use_proxy,
                          debugging_id=debugging_id, binary_response=binary_response)
        req = self.add_headers(req, headers)

        return self.send(req, grep=grep)

    def get_remote_file_size(self, req, cache=True):
        """
        This method was previously used in the framework to perform a HEAD
        request before each GET/POST (ouch!) and get the size of the response.
        The bad thing was that I was performing two requests for each
        resource... I moved the "protection against big files" to the
        keepalive.py module.

        I left it here because maybe I want to use it at some point. Mainly
        to call it directly.

        :return: The file size of the remote file.
        """
        res = self.HEAD(req.get_full_url(), headers=req.headers,
                        data=req.get_data(), cache=cache)

        content_length, _ = res.get_headers().iget('content-length', None)

        if content_length is None:
            msg = ('The HTTP response did not contain a content-length header.'
                   ' Unable to return the remote file size of request.'
                   ' (id:%s, did:)')
            args = (res.id, req.debugging_id)
            om.out.debug(msg % args)
            # I prefer to fetch the file, before this om.out.debug was a
            # "raise BaseFrameworkException", but this didn't make much sense
            return 0

        if content_length.isdigit():
            return int(content_length)

        msg = ('The content-length header value for the HTTP response is'
               ' not an integer, this is strange!'
               ' The value is: "%s" (id:%s, did:%s)')
        args = (content_length, req.id, req.debugging_id)
        om.out.error(msg % args)
        raise HTTPRequestException(msg, request=req)

    def __getattr__(self, method_name):
        """
        This is a "catch-all" way to be able to handle every HTTP method.

        :param method_name: The name of the method being called:
        xurllib_instance.OPTIONS will make method_name == 'OPTIONS'.
        """
        def any_method(uri_opener, method, uri, data=None, headers=Headers(),
                       cache=False, grep=True, cookies=True, session=None,
                       error_handling=True, timeout=None, use_basic_auth=True,
                       use_proxy=True,
                       follow_redirects=False,
                       debugging_id=None,
                       new_connection=False,
                       respect_size_limit=None,
                       binary_response=False):
            """
            :return: An HTTPResponse object that's the result of sending
                     the request with a method different from GET or POST.
            """
            if not isinstance(uri, URL):
                raise TypeError('The uri parameter of any_method must be'
                                ' of url.URL type.')

            if not isinstance(headers, Headers):
                raise TypeError('The headers parameter of any_method must be'
                                ' of Headers type.')

            uri_opener.setup()

            max_retries = uri_opener.settings.get_max_retrys()

            host = uri.get_domain()
            timeout = uri_opener.get_timeout(host) if timeout is None else timeout
            req = HTTPRequest(uri, data, cookies=cookies, session=session,
                              cache=cache,
                              method=method,
                              error_handling=error_handling,
                              retries=max_retries,
                              timeout=timeout,
                              new_connection=new_connection,
                              use_basic_auth=use_basic_auth,
                              follow_redirects=follow_redirects,
                              use_proxy=use_proxy,
                              debugging_id=debugging_id,
                              binary_response=binary_response)
            req = uri_opener.add_headers(req, headers or {})
            return uri_opener.send(req, grep=grep)

        method_partial = functools.partial(any_method, self, method_name)
        method_partial.__doc__ = 'Send %s HTTP request' % method_name
        return method_partial

    def _track_rtt(self, http_response, debugging_id):
        """
        Add the RTT associated with this response to the sum of all RTTs sent
        during this debugging_id.

        :param http_response: The HTTP response that is going out to the caller
        :param debugging_id: The debugging_id (if any) associated with the request
        :return: None
        """
        if not debugging_id:
            return

        if not http_response:
            return

        if not hasattr(http_response, 'get_wait_time'):
            return

        rtt = http_response.get_wait_time()
        if not rtt:
            return

        rtt_sum = self._rtt_sum_debugging_id.get(debugging_id, default=None)
        if rtt_sum is None:
            self._rtt_sum_debugging_id[debugging_id] = rtt
        else:
            self._rtt_sum_debugging_id[debugging_id] = rtt_sum + rtt

    def get_rtt_for_debugging_id(self, debugging_id):
        if debugging_id is None:
            return

        return self._rtt_sum_debugging_id.get(debugging_id, default=None)

    def add_headers(self, req, headers=Headers()):
        """
        Add all custom Headers() if they exist
        """
        for h, v in self.settings.header_list:
            req.add_header(h, v)

        for h, v in headers.iteritems():
            req.add_header(h, v)

        if self.settings.rand_user_agent is True:
            req.add_header('User-Agent', get_random_user_agent())

        return req

    def assert_allowed_proto(self, req):
        full_url = req.get_full_url().lower()

        if not full_url.startswith('http'):
            msg = 'Unsupported URL: "%s"'
            raise HTTPRequestException(msg % req.get_full_url(), request=req)

    def send(self, req, grep=True):
        """
        Actually send the request object.

        :param req: The HTTPRequest object that represents the request.
        :param grep: Should grep the HTTP request / response
        :return: An HTTPResponse object.
        """
        # This is the place where pause and stop are implemented
        self._before_send_hook(req)

        # Sanitize the URL
        self.assert_allowed_proto(req)

        # Evasion
        req = self._evasion(req)
        original_url = req._Request__original
        original_url_inst = req.url_object
        
        try:
            res = self._opener.open(req)
        except urllib2.HTTPError, e:
            # We usually get here when response codes in [404, 403, 401,...]
            return self._handle_send_success(req, e, grep, original_url,
                                             original_url_inst)

        except (socket.error,
                URLTimeoutError,
                ConnectionPoolException,
                OpenSSL.SSL.Error,
                OpenSSL.SSL.SysCallError,
                OpenSSL.SSL.ZeroReturnError,
                BadStatusLine), e:
            return self._handle_send_socket_error(req, e, grep, original_url)
        
        except (urllib2.URLError, httplib.HTTPException, HTTPRequestException), e:
            return self._handle_send_urllib_error(req, e, grep, original_url)
        
        else:
            return self._handle_send_success(req, res, grep, original_url,
                                             original_url_inst)

    def _decrease_worker_pool_size(self):
        w3af_core = self.get_w3af_core()
        worker_pool = w3af_core.worker_pool
        min_workers = w3af_core.MIN_WORKER_THREADS

        error_rate = self.get_error_rate()

        # Note that we decrease by two here, and increase by one below
        new_worker_count = worker_pool.get_worker_count() - 2
        new_worker_count = max(new_worker_count, min_workers)

        if new_worker_count >= min_workers:
            worker_pool.set_worker_count(new_worker_count)
            msg = 'Decreased the worker pool size to %s (error rate: %i%%)'
        else:
            msg = ('Not decreasing the worker pool size since it is lower'
                   ' than the min value required by w3af: %s (error rate:'
                   ' %i%%)')

        om.out.debug(msg % (new_worker_count, error_rate))

    def _increase_worker_pool_size(self):
        w3af_core = self.get_w3af_core()
        worker_pool = w3af_core.worker_pool
        max_workers = w3af_core.MAX_WORKER_THREADS

        error_rate = self.get_error_rate()

        # Note that we increase by one here, and decrease by two above
        new_worker_count = worker_pool.get_worker_count() + 1
        new_worker_count = min(new_worker_count, max_workers)

        if new_worker_count <= max_workers:
            worker_pool.set_worker_count(new_worker_count)
            msg = 'Increased the worker pool size to %s (error rate: %i%%)'
            om.out.debug(msg % (new_worker_count, error_rate))
        else:
            msg = 'Not increasing the worker pool size since it exceeds the max: %s'
            om.out.debug(msg % max_workers)

    def _should_increase_worker_pool(self):
        """
        We want to be very strict here, do not increase the worker pool
        size when there are "some errors". Just increase when there are
        "almost no errors"
        """
        error_rate = self.get_error_rate()
        if error_rate >= (ACCEPTABLE_ERROR_RATE / 4.0):
            return False

        return True

    def _should_decrease_worker_pool_size(self):
        error_rate = self.get_error_rate()
        if error_rate >= (ACCEPTABLE_ERROR_RATE / 2.0):
            return True

        return False

    def _handle_worker_pool_size(self):
        """
        Increase or decrease the worker pool size
        :return: None
        """
        if not self.has_w3af_core():
            return

        if not self._should_adjust_workers():
            return

        if self._should_decrease_worker_pool_size():
            self._decrease_worker_pool_size()

        elif self._should_increase_worker_pool():
            self._increase_worker_pool_size()

    def _should_adjust_workers(self):
        """
        :return: True if we should decrease the number of workers. The
                 idea behind this is to give the framework time to adjust
                 to the new thread pool size.

                 We usually see ~10 ConnectionPoolExceptions being raised
                 at the same time, thus we only want to react to the first
                 one and give the framework time to see what happens.
        """
        with self._should_adjust_workers_lock:
            if self._last_call_to_adjust_workers is None:
                self._last_call_to_adjust_workers = time.time()
                return True

            elif (time.time() - self._last_call_to_adjust_workers) >= 45:
                self._last_call_to_adjust_workers = time.time()
                return True

            return False

    def _handle_send_socket_error(self, req, exception, grep, original_url):
        """
        This error handling is separated from the other because we want to have
        better handling for:
            * Connection timeouts
            * Connection resets
            * Network problems (network connection goes down for some seconds)

        Our strategy for handling these errors is simple
        """
        self._increase_timeout_on_error(req, exception)

        return self._generic_send_error_handler(req,
                                                exception,
                                                grep,
                                                original_url)
        
    def _handle_send_urllib_error(self, req, exception, grep, original_url):
        """
        I get to this section of the code if a 400 error is returned
        also possible when a proxy is configured and not available
        also possible when auth credentials are wrong for the URI
        """
        return self._generic_send_error_handler(req,
                                                exception,
                                                grep,
                                                original_url)
        
    def _generic_send_error_handler(self, req, exception, grep, original_url):
        if not req.error_handling:
            msg = (u'Raising HTTP error "%s" "%s" failed reason: "%s".'
                   u' Error handling was disabled for this request (did:%s).')
            args = (req.get_method(), original_url, exception, req.debugging_id)
            om.out.debug(msg % args)

            error_str = get_exception_reason(exception) or str(exception)
            raise HTTPRequestException(error_str, request=req)

        with self._count_lock:
            self._log_failed_response(req, exception, original_url)

            if self._should_stop_scan(req):
                self._handle_error_count_exceeded(exception)

        self._handle_worker_pool_size()

        # Then retry!
        req._Request__original = original_url
        return self._retry(req, grep, exception)
    
    def _handle_send_success(self, req, res, grep, original_url,
                             original_url_inst):
        """
        Handle the case in "def _send" where the request was successful and
        we were able to get a valid HTTP response.
        
        :return: An HTTPResponse object.
        """
        # Everything went well!
        rdata = req.get_data()
        if not rdata:
            msg = ('%s %s returned HTTP code "%s"' %
                   (req.get_method(),
                    urllib.unquote_plus(original_url),
                    res.code))
        else:
            printable_data = urllib.unquote_plus(rdata)
            if len(rdata) > 75:
                printable_data = '%s...' % printable_data[:75]
                printable_data = printable_data.replace('\n', ' ')
                printable_data = printable_data.replace('\r', ' ')
                
            msg = ('%s %s with data: "%s" returned HTTP code "%s"'
                   % (req.get_method(),
                      original_url,
                      printable_data,
                      res.code))

        from_cache = hasattr(res, 'from_cache') and res.from_cache

        http_resp = HTTPResponse.from_httplib_resp(res,
                                                   original_url=original_url_inst,
                                                   binary_response=req.with_binary_response())
        http_resp.set_id(res.id)
        http_resp.set_from_cache(from_cache)
        http_resp.set_debugging_id(req.debugging_id)

        args = (res.id, from_cache, grep, http_resp.get_wait_time(), req.debugging_id)
        flags = ' (id=%s,from_cache=%i,grep=%i,rtt=%.2f,did=%s)' % args

        msg += flags
        om.out.debug(msg)

        # Clear the log of failed requests; this request is DONE!
        self._log_successful_response(http_resp)
        self._track_rtt(res, req.debugging_id)
        self._handle_worker_pool_size()

        if grep:
            self._grep(req, http_resp)

        return http_resp

    def _retry(self, req, grep, url_error):
        """
        Try to send the request again while doing some error handling.
        """
        req.retries_left -= 1

        if req.retries_left > 0:
            msg = 'Re-sending request "%s" (did:%s) after initial exception: "%s"'
            args = (req, req.debugging_id, url_error)
            om.out.debug(msg % args)

            # Before sending it again we update the timeout, which could have
            # changed because of the error we just found
            host = req.get_host()
            req.set_timeout(self.get_timeout(host))

            return self.send(req, grep=grep)
        
        else:
            # Please note that I'm raising HTTPRequestException and not a
            # ScanMustStopException (or subclasses) since I don't want the
            # scan to stop because of a single HTTP request failing.
            #
            # Actually we get here if one request fails three times to be sent
            # but that might be because of the http request itself and not a
            # fault of the framework/server/network.
            error_str = get_exception_reason(url_error) or str(url_error)
            raise HTTPRequestException(error_str, request=req)

    def _log_failed_response(self, request, exception, original_url):
        """
        Add the failed response to the self._last_responses log, and if we got a
        lot of failures raise a "ScanMustStopException" subtype.

        :param exception: Exception object.
        """
        # Log the exception
        msg = u'Failed to HTTP "%s" "%s". Reason: "%s", going to retry (did:%s)'

        original_url = smart_unicode(original_url)
        args = (request.get_method(), original_url, exception, request.debugging_id)

        om.out.debug(msg % args)

        # Don't make a lot of noise on URLTimeoutError which is pretty common
        # and properly handled by this library
        no_traceback_for = (URLTimeoutError,
                            ConnectionPoolException,
                            BadStatusLine,
                            socket.error,
                            OpenSSL.SSL.SysCallError,
                            OpenSSL.SSL.ZeroReturnError)
        if not isinstance(exception, no_traceback_for):
            msg = 'Traceback for this error: %s'
            om.out.debug(msg % traceback.format_exc())

        # Now we save the error to self._last_responses for tracking and
        # statistics
        reason = get_exception_reason(exception)
        reason = reason or str(exception)

        host = request.get_domain()

        # The HTTP request failed, this most likely means that we received a
        # timeout or some other network / protocol error.
        #
        # We want to save the ResponseMeta with some RTT that indicates that
        # this (potential) timeout happen. Se we get the current timeout and
        # use it as the RTT parameter
        #
        # This is not perfect, BUT is better than not specifying any RTT.
        #
        # Specifying the `rtt` here will allow `get_average_rtt` to take these
        # errors into account when calculating the RTT
        rtt = self.get_timeout(host)

        self._last_responses.append(ResponseMeta(False,
                                                 reason,
                                                 host=host,
                                                 rtt=rtt))

        self._log_error_rate()

    def _should_stop_scan(self, request):
        """
        If the last MAX_ERROR_COUNT - 1 responses are errors then we check if
        the remote server root path is still reachable. If it is, we add
        (True, SUCCESS) to the last responses and continue; else we return False
        because we're in a case where:
              * The user's connection is dead
              * The remote server is unreachable

        :return: True if we should stop the scan due to too many consecutive
                 errors being received from the server.

        :see: https://github.com/andresriancho/w3af/issues/8698
        """
        #
        # We're looking for this pattern in the last_responses:
        #   True, False, False, False, ..., False
        #
        # Which means that at some point we were able to reach the remote server
        # but now we're having problems doing so and need to check if the remote
        # server is still reachable.
        #
        # Any other patterns we don't care in this method:
        #   False, True, False, True, False, True
        #       Unstable connection, _pause_on_http_error should help with it
        #
        #   True, True, True, False, False, False, ..., False
        #       Looks like the remote server is unreachable and we're going
        #       towards the pattern we look for, but nothing to do here for now
        #
        #   False, True, True, True, True, ..., True
        #       A server error and then it recovered, keep scanning.
        #
        # Note that we can only find the desired pattern if we lock the write
        # and check access to the _last_responses, otherwise the threads will
        # "break" it
        last_n_responses = list(self._last_responses)[-MAX_ERROR_COUNT:]
        first_result = last_n_responses[0]
        last_n_without_first = last_n_responses[1:]

        if len(last_n_without_first) != (MAX_ERROR_COUNT - 1):
            # Not enough last_responses to tell if we should stop the scan
            return False

        all_following_failed = True

        for response_meta in last_n_without_first:
            if response_meta.successful:
                all_following_failed = False
                break

        if first_result.successful and all_following_failed:
            # Found the pattern we were looking for, we want to test if the
            # remote server is reachable
            if self._server_root_path_is_reachable(request):
                # We don't need to add (True, SUCCESS) to the last_responses
                # manually since in _server_root_path_is_reachable we use _send
                # which (on success) calls _log_successful_response and does
                # that for us
                return False

            # Stop the scan!
            return True

        # If we don't find the pattern we look for, then we just continue with
        # the scan as usual
        return False

    def _server_root_path_is_reachable(self, request):
        """
        Sends an HTTP GET to the server's root path to verify that it's
        reachable from our location.

        :param request: The original HTTP request
        :return: True if we were able to get a response
        """
        uri = request.get_uri()
        root_url = uri.base_url()
        host = uri.get_domain()

        # We drastically increase the timeout for this request. What
        # could have happen is that w3af lowered the timeout for HTTP
        # responses in a very aggressive way and then sent many HTTP
        # requests at the same time. Those requests failed due to the
        # aggressive timeout which lead to multiple sequential failures
        #
        # When multiple failures are detected, w3af tries to check if
        # the remote site is still up using this method. If we don't
        # increase the timeout like this we'll still use the incorrectly
        # set timeout, which would (one more time) trigger an error.
        # Sadly this time the error would be fatal since the scan would
        # stop.
        timeout = self.get_timeout(host) * 4
        self.set_timeout(timeout, host)

        req = HTTPRequest(root_url,
                          cookies=True, cache=False,
                          error_handling=False, method='GET',
                          retries=0, timeout=timeout)
        req = self.add_headers(req)

        try:
            self.send(req, grep=False)
        except HTTPRequestException, e:
            msg = 'Remote URL %s is UNREACHABLE due to: "%s"'
            om.out.debug(msg % (root_url, e))
            return False
        except Exception, e:
            msg = 'Internal error makes URL %s UNREACHABLE due to: "%s"'
            om.out.debug(msg % (root_url, e))
            return False
        else:
            msg = 'Remote URL %s is reachable'
            om.out.debug(msg % root_url)
            return True

    def get_error_rate(self):
        """
        :return: The error rate as an integer 0-100
        """
        last_responses = list(self._last_responses)
        total_failed = 0.0
        total = len(last_responses)

        if total == 0:
            return total

        for response_meta in last_responses:
            if not response_meta.successful:
                total_failed += 1

        return int((total_failed / total) * 100)

    def _log_error_rate(self):
        """
        Logs the error rate to the debug() log, useful to understand why a scan
        fails with "Too many consecutive errors"

        :see: https://github.com/andresriancho/w3af/issues/8698
        """
        error_rate = self.get_error_rate()
        om.out.debug('ExtendedUrllib error rate is at %i%%' % error_rate)

    def _handle_error_count_exceeded(self, error):
        """
        Handle the case where we exceeded MAX_ERROR_COUNT
        """
        # Create a detailed exception message
        msg = ('w3af found too many consecutive errors while performing'
               ' HTTP requests. In most cases this means that the remote web'
               ' server is not reachable anymore, the network is down, or'
               ' a WAF is blocking our tests. The last exception message'
               ' was "%s" (%s.%s).')

        reason_msg = get_exception_reason(error)
        args = (error,
                error.__class__.__module__,
                error.__class__.__name__)

        # If I got a reason, it means that it is a known exception.
        if reason_msg is not None:
            # Stop using ExtendedUrllib instance
            e = ScanMustStopByKnownReasonExc(msg % args, reason=reason_msg)

        else:
            last_errors = []
            last_n_responses = list(self._last_responses)[-MAX_ERROR_COUNT:]

            for response_meta in last_n_responses:
                last_errors.append(response_meta.message)

            e = ScanMustStopByUnknownReasonExc(msg % args, errs=last_errors)

        om.out.debug('The extended urllib will raise a scan must stop exception'
                     ' for each request after this message. The remote server is'
                     ' unreachable.')
        self._stop_exception = e

        # pylint: disable=E0702
        raise self._stop_exception
        # pylint: enable=E0702

    def _log_successful_response(self, response):
        host = response.get_url().get_domain()
        self._last_responses.append(ResponseMeta(True,
                                                 SUCCESS,
                                                 rtt=response.get_wait_time(),
                                                 host=host))

    def set_grep_queue_put(self, grep_queue_put):
        self._grep_queue_put = grep_queue_put

    def set_evasion_plugins(self, evasion_plugins):
        # I'm sorting evasion plugins based on priority
        def sort_func(x, y):
            return cmp(x.get_priority(), y.get_priority())
        evasion_plugins.sort(sort_func)

        # Save the info
        self._evasion_plugins = evasion_plugins

    def _evasion(self, request):
        """
        :param request: HTTPRequest instance that is going to be modified
        by the evasion plugins
        """
        for eplugin in self._evasion_plugins:
            try:
                request = eplugin.modify_request(request)
            except BaseFrameworkException, e:
                msg = 'Evasion plugin "%s" failed to modify the request: "%s"'
                args = (eplugin.get_name(), e)
                om.out.error(msg % args)

        return request

    def _grep(self, request, response):
        if self._grep_queue_put is None:
            return

        self._grep_queue_put(request, response)


@contextmanager
def raise_size_limit(respect_size_limit):
    """
    TODO: This is an UGLY hack that allows me to download over-sized files,
          but it shouldn't be implemented like this! It should look more
          like the cookies attribute/parameter which uses the cookie_handler.
    """
    if not respect_size_limit:
        original_size = cf.cf.get('max_file_size')
        cf.cf.save('max_file_size', 10 ** 10)
    
        yield

        cf.cf.save('max_file_size', original_size)
    else:
        yield
