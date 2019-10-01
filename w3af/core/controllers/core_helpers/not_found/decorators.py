"""
decorators.py

Copyright 2018 Andres Riancho

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
import threading
import functools

# pylint: disable=E0401
from darts.lib.utils.lru import LRUDict
# pylint: enable=E0401

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.core_helpers.not_found.response import FourOhFourResponse
from w3af.core.data.misc.response_cache_key import quick_hash, ResponseCacheKeyCache
from w3af.core.data.fuzzer.utils import rand_alnum


class Decorator(object):
    def __get__(self, instance, instancetype):
        # https://stackoverflow.com/questions/5469956/python-decorator-self-is-mixed-up
        return functools.partial(self.__call__, instance)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class LRUCache404(Decorator):
    """
    This decorator caches the 404 responses to reduce CPU usage and,
    in some cases, HTTP requests being sent.
    """

    MAX_IN_MEMORY_RESULTS = 5000
    STATS_EVERY = 50

    def __init__(self, _function):
        self._function = _function

        # The performance impact of storing many items in the cached
        # (in memory) part of the CachedDiskDict is low. The keys for
        # this cache are hashes and the values are booleans
        #
        # Using the LRUDict instead of SynchronizedLRUDict because this decorator
        # is run wrapped around PreventMultipleThreads, and also because we're
        # consuming it in a way where thread-generated race condition errors can
        # be ignored (they do not generate a big impact)
        #
        # LRUDict is faster than SynchronizedLRUDict because there are no locks
        self._is_404_by_url_lru = LRUDict(capacity=self.MAX_IN_MEMORY_RESULTS)
        self._is_404_by_body_lru = LRUDict(capacity=self.MAX_IN_MEMORY_RESULTS)

        self._stats_from_cache = 0.0
        self._stats_total = 0.0

        self._response_cache_key_cache = ResponseCacheKeyCache()

    def __call__(self, *args, **kwargs):
        http_response = args[1]
        query = args[2]

        self._stats_total += 1
        self._log_stats(http_response)

        url_cache_key = self.get_url_cache_key(http_response)

        try:
            result = self._is_404_by_url_lru.get(url_cache_key, None)
        except (AttributeError, AssertionError, KeyError) as _:
            # This is a rare race conditions which happens when another
            # thread modifies the cache and changes the __first item in
            # the cache.
            result = None
            
        if result is not None:
            self._log_success(http_response, result, 'URL')
            return result

        body_cache_key = self._response_cache_key_cache.get_response_cache_key(http_response,
                                                                               clean_response=query)

        try:
            result = self._is_404_by_body_lru.get(body_cache_key, None)
        except (AttributeError, AssertionError, KeyError) as _:
            # This is a rare race conditions which happens when another
            # thread modifies the cache and changes the __first item in
            # the cache.
            result = None

        if result is not None:
            self._log_success(http_response, result, 'body')
            return result

        # Run the real is_404 function
        result = self._function(*args, **kwargs)

        # Save the result to both caches
        try:
            self._is_404_by_body_lru[body_cache_key] = result
        except (AttributeError, AssertionError, KeyError) as _:
            # This is a rare race conditions which happens when another
            # thread modifies the cache and changes the __first item in
            # the cache.
            pass

        try:
            self._is_404_by_url_lru[url_cache_key] = result
        except (AttributeError, AssertionError, KeyError) as _:
            # This is a rare race conditions which happens when another
            # thread modifies the cache and changes the __first item in
            # the cache.
            pass

        return result

    def _log_stats(self, http_response):
        if self._stats_total % self.STATS_EVERY == 0:
            rate = self._stats_from_cache / self._stats_total * 100
            om.out.debug('The 404 cache has a %.2f %% hit rate' % rate)

    def _log_success(self, http_response, result, cache_name):
        self._stats_from_cache += 1

        response_did = http_response.get_debugging_id()
        debugging_id = response_did if response_did is not None else rand_alnum(8)

        is_is_not = 'is a 404' if result else 'is NOT a 404'

        msg = '"%s" (id:%s, code:%s, len:%s, did:%s) %s [%s 404 cache]'
        args = (http_response.get_url(),
                http_response.id,
                http_response.get_code(),
                len(http_response.get_body()),
                debugging_id,
                is_is_not,
                cache_name)
        om.out.debug(msg % args)

        return False

    @staticmethod
    def get_url_cache_key(http_response):
        """
        :param http_response: The http response
        :return: md5 hash of the HTTP response URI (binary form)
        """
        return quick_hash(http_response.get_uri().url_string)


class PreventMultipleThreads(Decorator):
    """
    This decorator tracks executions of is_404(), if one of those executions
    is running with parameter X, and new one call is made to is_404() with the
    same parameter (*), then the decorator forces the second caller to wait until
    the first execution is completed.

    (*) The way we compare parameters for is_404() here is not by string equals,
        we normalize the paths of each HTTP response and then compare them.

        This makes sure that we don't send unnecessary HTTP requests when
        running is_404() on an HTTP response for http://foo.com/phpinfo.php
        and another for http://foo.com/test.php

    The second execution will then run, query the cache, and get the result.

    Without this decorator two executions would run, consume CPU, in some cases
    send HTTP requests, and finally both were going to write the same result
    to the cache.

    This issue could be seen in the debug logs as:

        [Thu Oct 11 10:18:24 2018 - debug] GET https://host/SP8Bund2/ returned HTTP code "404" ...
        [Thu Oct 11 10:18:24 2018 - debug] GET https://host/KKJCnk08/ returned HTTP code "404" ...
        [Thu Oct 11 10:18:24 2018 - debug] GET https://host/PfOoZiAF/ returned HTTP code "404" ...
        [Thu Oct 11 10:18:24 2018 - debug] GET https://host/Pg6Uuid1/ returned HTTP code "404" ...
        [Thu Oct 11 10:18:24 2018 - debug] GET https://host/y4FeR1lB/ returned HTTP code "404" ...

    Notice the same timestamp in each line, and the 8 random chars being sent in the
    directory, which is part of the is_404() algorithm.
    """

    # in seconds
    TIMEOUT = 240

    def __init__(self, _function):
        self._function = _function
        self._404_call_events = {}

    def __call__(self, *args, **kwargs):
        http_response = args[1]

        call_key = self.get_call_key(http_response)

        event = self._404_call_events.get(call_key, None)

        if event is None:
            # There is no current execution of is_404 with these parameters
            #
            # Create a new event and save it to the dict, then call the wrapped
            # function and set() the event so anyone waiting() on it will be
            # released
            event = threading.Event()
            self._404_call_events[call_key] = event

            try:
                return self._function(*args, **kwargs)
            finally:
                event.set()
                self._404_call_events.pop(call_key, None)

        else:
            # Another thread is already running is_404 on the same URL path
            # we better wait for a while
            start = time.time()

            wait_result = event.wait(timeout=self.TIMEOUT)

            spent = time.time() - start

            response_did = http_response.get_debugging_id()
            msg_args = (spent, id(event), call_key, response_did)
            msg = ('Waited %.2f seconds in PreventMultipleThreads for event %s'
                   ' and normalized path %s (did:%s)')
            om.out.debug(msg % msg_args)

            if not wait_result:
                # Something really bad happen. The is_404() function should
                # never take more than TIMEOUT seconds to process one HTTP
                # response.
                #
                # To prevent more issues during the scan we're going to return
                # True here, meaning that the is_404() will return True without
                # even being called.
                #
                # This will reduce the processing / HTTP requests, etc. for a
                # scan that is most likely having really bad performance.
                msg = ('is_404() took more than %s seconds to run on %s,'
                       ' returning true to reduce CPU usage and HTTP requests.'
                       ' This error is very rare and should be manually analyzed.')
                args = (self.TIMEOUT, http_response.get_uri())
                om.out.error(msg % args)
                return True
            else:
                # All right! is_404 function call is complete, now let's call
                # it again to obtain the result from the cache
                return self._function(*args, **kwargs)

    def get_call_key(self, http_response):
        return FourOhFourResponse.normalize_path(http_response.get_uri())
