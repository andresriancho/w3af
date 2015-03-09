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
import httplib
import socket
import threading
import time
import traceback
import urllib
import urllib2
import OpenSSL

from contextlib import contextmanager
from collections import deque

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf
import opener_settings

from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              ConnectionPoolException,
                                              HTTPRequestException,
                                              ScanMustStopByUnknownReasonExc,
                                              ScanMustStopByKnownReasonExc,
                                              ScanMustStopByUserRequest)
from w3af.core.data.parsers.http_request_parser import http_request_parser
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.handlers.keepalive import URLTimeoutError
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.user_agent.random_user_agent import get_random_user_agent
from w3af.core.data.url.helpers import get_clean_body, get_exception_reason
from w3af.core.data.url.response_meta import ResponseMeta, SUCCESS
from w3af.core.data.url.constants import (MAX_ERROR_COUNT,
                                          MAX_RESPONSE_COLLECT,
                                          SOCKET_ERROR_DELAY,
                                          TIMEOUT_MULT_CONST,
                                          ADJUST_LIMIT)


class ExtendedUrllib(object):
    """
    This is a urllib2 wrapper.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        self.settings = opener_settings.OpenerSettings()
        self._opener = None

        # For error handling
        self._last_responses = deque(maxlen=MAX_RESPONSE_COLLECT)
        self._count_lock = threading.RLock()

        # For rate limiting
        self._rate_limit_last_time_called = 0.0
        self._rate_limit_lock = threading.RLock()

        # For timeout auto adjust
        self._total_requests = 0

        # User configured options (in an indirect way)
        self._grep_queue_put = None
        self._evasion_plugins = []
        self._user_paused = False
        self._user_stopped = False
        self._stop_exception = None

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

    def _before_send_hook(self, request):
        """
        This is a method that is called before every request is sent. I'm using
        it as a hook implement:
            - The pause/stop feature
            - Memory debugging features
        """
        self._pause_and_stop()
        self._pause_on_http_error(request)
        self._rate_limit()
        self._auto_adjust_timeout()

        # Increase the request count
        self._total_requests += 1

    def _auto_adjust_timeout(self):
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
        if not self._should_auto_adjust_now():
            return

        average_rtt, num_samples = self.get_average_rtt(ADJUST_LIMIT)

        if num_samples < (ADJUST_LIMIT / 2):
            msg = 'Not enough samples collected (%s) to adjust timeout.' \
                  ' Keeping the current value of %s seconds'
            om.out.debug(msg % (num_samples, self.settings.get_timeout()))
        else:
            timeout = average_rtt * TIMEOUT_MULT_CONST
            self.settings.set_timeout(timeout)

    def get_average_rtt(self, count=ADJUST_LIMIT):
        """
        :param count: The number of HTTP requests to sample the RTT from
        :return: Tuple with (average RTT from the last `count` requests,
                             the number of successful responses, which contain
                             an RTT, and were used to calculate the average RTT)
        """
        assert len(self._last_responses) >= count, 'Not enough samples'

        last_n_responses = list(self._last_responses)[-count:]
        rtt_sum = 0.0
        add_count = 0

        for response_meta in last_n_responses:
            if response_meta.rtt is not None:
                rtt_sum += response_meta.rtt
                add_count += 1

        average_rtt = float(rtt_sum) / add_count

        return average_rtt, add_count

    def _should_auto_adjust_now(self):
        """
        :return: True if we need to auto adjust the timeout now
        """
        if self.settings.get_configured_timeout() != 0:
            # The user disabled the timeout auto-adjust feature
            return False

        if self.get_total_requests() == 0:
            return False

        if self.get_total_requests() % ADJUST_LIMIT == 0:
            return True

        return False

    def get_total_requests(self):
        """
        :return: The number of requests sent (successful, timeout, failed, all
                 are counted here).
        """
        return self._total_requests

    def _pause_on_http_error(self, request):
        """
        This method will pause the scan for an increasing period of time based
        on the HTTP error rate. HTTP errors are timeouts, network unreachable,
        etc. things like 404, 403, 500 are NOT considered errors.

        The objective of this method is to give the remote server, or local
        connection, the chance to recover from their errors without killing the
        w3af scan.

        Successful requests lower the error rate and allow faster request rates.
        Failed requests increase the rate and make this method delay requests

        The rate is multiplied by SOCKET_ERROR_DELAY to get the real delay time
        in seconds.

        The error rate starts at zero, so no delay is added at the beginning

        In the worse case scenario, where MAX_ERROR_COUNT errors occur, the
        requests are going to be delayed as follows (considering MAX_ERROR_COUNT
        10 and SOCKET_ERROR_DELAY 0.1):
            1-  No delay
            2-  SOCKET_ERROR_DELAY * 1 == 0.1
            3-  SOCKET_ERROR_DELAY * 2 == 0.2
            ...
            10- SOCKET_ERROR_DELAY * 9 == 0.9

        The total time added by this method (considering the above values) is
        4.5 seconds. That's the time we give the remote server to recover.

        :return: None, but might delay the requests which go out to the network
        :see: https://github.com/andresriancho/w3af/issues/4811
        """
        error_rate = self.get_error_rate()
        if error_rate:
            self._rate_limit_lock.acquire()

            # Logging
            error_sleep = SOCKET_ERROR_DELAY * error_rate
            msg = 'Sleeping for %s seconds before sending HTTP request to' \
                  ' "%s" after receiving URL/socket error. The ExtendedUrllib' \
                  ' error rate is at %s%%.'
            args = (error_sleep, request.url_object, error_rate)
            om.out.debug(msg % args)

            # The actual delay
            time.sleep(error_sleep)

            self._rate_limit_lock.release()

    def _rate_limit(self):
        """
        Makes sure that we don't send more than X HTTP requests per seconds
        :return:
        """
        max_requests_per_second = self.settings.get_max_requests_per_second()

        if max_requests_per_second > 0:

            min_interval = 1.0 / float(max_requests_per_second)
            elapsed = time.clock() - self._rate_limit_last_time_called
            left_to_wait = min_interval - elapsed

            self._rate_limit_lock.acquire()

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            self._rate_limit_lock.release()

            self._rate_limit_last_time_called = time.clock()

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

            # There might be errors that make us stop the process, the exception
            # was already raised (see below) but we want to make sure that we
            # keep raising it until the w3afCore really stops.
            if self._stop_exception is not None:
                # pylint: disable=E0702
                raise self._stop_exception
                # pylint: enable=E0702

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

    def end(self):
        """
        This method is called when the ExtendedUrllib is not going to be used
        anymore.
        """
        self._opener = None
        self.clear()
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

    def get_headers(self, uri):
        """
        :param uri: The URI we want to know the request headers

        :return: A Headers object with the HTTP headers that would be added by
                the library when sending a request to uri.
        """
        req = HTTPRequest(uri)
        req = self._add_headers(req)
        return Headers(req.headers)

    def get_cookies(self):
        """
        :return: The cookies that this uri opener has collected during this scan
        """
        return self.settings.get_cookies()

    def send_clean(self, mutant):
        """
        Sends a mutant to the network (without using the cache) and then returns
        the HTTP response object and a sanitized response body (which doesn't
        contain any traces of the injected payload).

        The sanitized version is useful for having clean comparisons between two
        responses that were generated with different mutants.

        :param mutant: The mutant to send to the network.
        :return: (HTTP response,
                  Sanitized HTTP response body)
        """
        http_response = self.send_mutant(mutant, cache=False)
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
                    cookies=True, error_handling=True):
        """
        Sends a mutant to the remote web server.

        :param callback: If None, return the HTTP response object, else call
                         the callback with the mutant and the http response as
                         parameters.

        :return: The HTTPResponse object associated with the request
                 that was just sent.
        """
        #
        # IMPORTANT NOTE: If you touch something here, the whole framework may
        # stop working!
        #
        uri = mutant.get_uri()
        data = mutant.get_data()

        # Also add the cookie header; this is needed by the CookieMutant
        headers = mutant.get_all_headers()
        cookie = mutant.get_cookie()
        if cookie:
            headers['Cookie'] = str(cookie)

        args = (uri,)
        kwargs = {
            'data': data,
            'headers': headers,
            'grep': grep,
            'cache': cache,
            'cookies': cookies,
            'error_handling': error_handling,
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
            grep=True, cookies=True, respect_size_limit=True,
            error_handling=True):
        """
        HTTP GET a URI using a proxy, user agent, and other settings
        that where previously set in opener_settings.py .

        :param uri: This is the URI to GET, with the query string included.
        :param data: Only used if the uri parameter is really a URL. The data
                     will be converted into a string and set as the URL object
                     query string before sending.
        :param headers: Any special headers that will be sent with this request
        :param cache: Should the library search the local cache for a response
                      before sending it to the wire?
        :param grep: Should grep plugins be applied to this request/response?
        :param cookies: Send stored cookies in request (or not)

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

        if data:
            uri = uri.copy()
            uri.querystring = data

        req = HTTPRequest(uri, cookies=cookies, cache=cache,
                          error_handling=error_handling, method='GET',
                          retries=self.settings.get_max_retrys())
        req = self._add_headers(req, headers)

        with raise_size_limit(respect_size_limit):
            return self._send(req, grep=grep)

    def POST(self, uri, data='', headers=Headers(), grep=True, cache=False,
             cookies=True, error_handling=True):
        """
        POST's data to a uri using a proxy, user agents, and other settings
        that where set previously.

        :param uri: This is the url where to post.
        :param data: A string with the data for the POST.
        :return: An HTTPResponse object.
        """
        if not isinstance(uri, URL):
            raise TypeError('The uri parameter of ExtendedUrllib.POST() must'
                            ' be of url.URL type.')

        if not isinstance(headers, Headers):
            raise TypeError('The header parameter of ExtendedUrllib.POST() must'
                            ' be of Headers type.')

        #    Validate what I'm sending, init the library (if needed)
        self.setup()

        #
        #    Create and send the request
        #
        #    Please note that the cache=False overrides the user setting
        #    since we *never* want to return cached responses for POST
        #    requests.
        #
        data = str(data)

        req = HTTPRequest(uri, data=data, cookies=cookies, cache=False,
                          error_handling=error_handling, method='POST',
                          retries=self.settings.get_max_retrys())
        req = self._add_headers(req, headers)

        return self._send(req, grep=grep)

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

        resource_length = None
        for i in res.get_headers():
            if i.lower() == 'content-length':
                resource_length = res.get_headers()[i]
                if resource_length.isdigit():
                    resource_length = int(resource_length)
                else:
                    msg = 'The content length header value of the response'\
                          ' wasn\'t an integer, this is strange... The value'\
                          ' is: "%s".'
                    om.out.error(msg % res.get_headers()[i])
                    raise HTTPRequestException(msg, request=req)

        if resource_length is not None:
            return resource_length
        else:
            msg = 'The response didn\'t contain a content-length header.'\
                  ' Unable to return the remote file size of request with'\
                  ' id: %s' % res.id
            om.out.debug(msg)
            # I prefer to fetch the file, before this om.out.debug was a
            # "raise BaseFrameworkException", but this didn't make much sense
            return 0

    def __getattr__(self, method_name):
        """
        This is a "catch-all" way to be able to handle every HTTP method.

        :param method_name: The name of the method being called:
        xurllib_instance.OPTIONS will make method_name == 'OPTIONS'.
        """
        class AnyMethod(object):

            def __init__(self, xu, method):
                self._xurllib = xu
                self._method = method

            def __call__(self, uri, data=None, headers=Headers(), cache=False,
                         grep=True, cookies=True, error_handling=True):
                """
                :return: An HTTPResponse object that's the result of
                    sending the request with a method different from
                    "GET" or "POST".
                """
                if not isinstance(uri, URL):
                    raise TypeError('The uri parameter of AnyMethod.'
                                    '__call__() must be of url.URL type.')

                if not isinstance(headers, Headers):
                    raise TypeError('The headers parameter of AnyMethod.'
                                    '__call__() must be of Headers type.')

                self._xurllib.setup()

                max_retries = self._xurllib.settings.get_max_retrys()

                req = HTTPRequest(uri, data, cookies=cookies, cache=cache,
                                  method=self._method,
                                  error_handling=error_handling,
                                  retries=max_retries)
                req = self._xurllib._add_headers(req, headers or {})
                return self._xurllib._send(req, grep=grep)

        return AnyMethod(self, method_name)

    def _add_headers(self, req, headers=Headers()):
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

    def _check_uri(self, req):
        if req.get_full_url().startswith('http'):
            return True

        elif req.get_full_url().startswith('javascript:') or \
        req.get_full_url().startswith('mailto:'):
            msg = 'Unsupported URL: "%s"'
            raise HTTPRequestException(msg % req.get_full_url(), request=req)

        else:
            return False

    def _send(self, req, grep=True):
        """
        Actually send the request object.

        :param req: The HTTPRequest object that represents the request.
        :return: An HTTPResponse object.
        """
        # This is the place where I hook the pause and stop feature
        self._before_send_hook(req)

        # Sanitize the URL
        self._check_uri(req)

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
        
        except (socket.error, URLTimeoutError,
                ConnectionPoolException, OpenSSL.SSL.SysCallError,
                OpenSSL.SSL.ZeroReturnError), e:
            return self._handle_send_socket_error(req, e, grep, original_url)
        
        except (urllib2.URLError, httplib.HTTPException, HTTPRequestException), e:
            return self._handle_send_urllib_error(req, e, grep, original_url)
        
        else:
            return self._handle_send_success(req, res, grep, original_url,
                                             original_url_inst)
    
    def _handle_send_socket_error(self, req, exception, grep, original_url):
        """
        This error handling is separated from the other because we want to have
        better handling for:
            * Connection timeouts
            * Connection resets
            * Network problems (network connection goes down for some seconds)

        Our strategy for handling these errors is simple
        """
        return self._generic_send_error_handler(req, exception, grep,
                                                original_url)
        
    def _handle_send_urllib_error(self, req, exception, grep, original_url):
        """
        I get to this section of the code if a 400 error is returned
        also possible when a proxy is configured and not available
        also possible when auth credentials are wrong for the URI
        """
        return self._generic_send_error_handler(req, exception, grep,
                                                original_url)
        
    def _generic_send_error_handler(self, req, exception, grep, original_url):
        if not req.error_handling:
            msg = 'Raising HTTP error "%s" "%s". Reason: "%s". Error handling' \
                  ' was disabled for this request.'
            om.out.debug(msg % (req.get_method(), original_url, exception))
            error_str = get_exception_reason(exception) or str(exception)
            raise HTTPRequestException(error_str, request=req)

        # Log the error
        msg = 'Failed to HTTP "%s" "%s". Reason: "%s", going to retry.'
        om.out.debug(msg % (req.get_method(), original_url, exception))

        # Don't make a lot of noise on URLTimeoutError which is pretty common
        # and properly handled by this library
        if not isinstance(exception, URLTimeoutError):
            msg = 'Traceback for this error: %s'
            om.out.debug(msg % traceback.format_exc())

        with self._count_lock:
            self._log_failed_response(exception, req)

            if self._should_stop_scan(req):
                self._handle_error_count_exceeded(exception)

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
        flags = ' (id=%s,from_cache=%i,grep=%i)' % (res.id, from_cache,
                                                    grep)
        msg += flags
        om.out.debug(msg)

        http_resp = HTTPResponse.from_httplib_resp(res,
                                                   original_url=original_url_inst)
        http_resp.set_id(res.id)
        http_resp.set_from_cache(from_cache)

        # Clear the log of failed requests; this request is DONE!
        self._log_successful_response(http_resp)

        if grep:
            self._grep(req, http_resp)

        return http_resp

    def _retry(self, req, grep, url_error):
        """
        Try to send the request again while doing some error handling.
        """
        req.retries_left -= 1

        if req.retries_left > 0:
            msg = 'Re-sending request "%s" after initial exception: "%s"'
            om.out.debug(msg % (req, url_error))
            return self._send(req, grep=grep)
        
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

    def _log_failed_response(self, error, request):
        """
        Add the failed response to the self._last_responses log, and if we got a
        lot of failures raise a "ScanMustStopException" subtype.

        :param error: Exception object.
        """
        reason = get_exception_reason(error)
        reason = reason or str(error)
        self._last_responses.append(ResponseMeta(False, reason))

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
        all_following_failed = True

        for response_meta in last_n_responses[1:]:
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

        req = HTTPRequest(root_url, cookies=True, cache=False,
                          error_handling=False, method='GET', retries=0)
        req = self._add_headers(req)

        try:
            self._send(req, grep=False)
        except HTTPRequestException, e:
            msg = 'Remote server is UNREACHABLE due to: "%s"'
            om.out.debug(msg % e)
            return False
        except Exception, e:
            msg = 'Internal error makes server UNREACHABLE due to: "%s"'
            om.out.debug(msg % e)
            return False
        else:
            msg = 'Remote server is reachable'
            om.out.debug(msg)
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
               ' a WAF is blocking our tests. The last exception message '
               'was "%s" (%s).')

        reason_msg = get_exception_reason(error)
        args = (error, error.__class__.__name__)

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

        self._stop_exception = e
        # pylint: disable=E0702
        raise self._stop_exception
        # pylint: enable=E0702

    def _log_successful_response(self, response):
        self._last_responses.append(ResponseMeta(True,
                                                 SUCCESS,
                                                 response.get_wait_time()))

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
                msg = 'Evasion plugin "%s" failed to modify the request.'\
                      ' Exception: "%s".'
                om.out.error(msg % (eplugin.get_name(), e))

        return request

    def _grep(self, request, response):

        url_instance = request.url_object
        domain = url_instance.get_domain()

        if self._grep_queue_put is not None and\
        domain in cf.cf.get('target_domains'):

            # Create a fuzzable request based on the urllib2 request object
            headers_inst = Headers(request.header_items())
            fr = FuzzableRequest.from_parts(url_instance,
                                            request.get_method(),
                                            request.get_data() or '',
                                            headers_inst)

            self._grep_queue_put((fr, response))


@contextmanager
def raise_size_limit(respect_size_limit):
    """
    TODO: This is an UGLY hack that allows me to download oversized files,
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
