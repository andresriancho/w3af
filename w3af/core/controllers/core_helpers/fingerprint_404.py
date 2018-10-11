"""
fingerprint_404.py

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
from __future__ import with_statement

import copy
import thread
import threading
import itertools
import functools

from functools import wraps
from collections import deque

# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.data.dc.headers import Headers
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.url.helpers import get_clean_body_impl, NO_CONTENT_MSG
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter

from w3af.core.controllers.misc.generate_404_filename import generate_404_filename
from w3af.core.controllers.misc.decorators import retry
from w3af.core.controllers.misc.fuzzy_string_cmp import (fuzzy_equal,
                                                         fuzzy_equal_return_distance,
                                                         relative_distance,
                                                         upper_bound_similarity)
from w3af.core.controllers.exceptions import (HTTPRequestException,
                                              FourOhFourDetectionException)


IS_EQUAL_RATIO = 0.90
MUST_VERIFY_RATIO = 0.75
MAX_404_RESPONSES = 50
CLEAN_DB_EVERY = 10
MIN_SCORE_FOR_404 = 2

COMMON_404_WORDS = [
    'not found',
    'not find',
    'no encontrada',
    'error',
    'unexpected',
    'server',
    'support',
    'request',
    'handled',
    '404',
    'error 404',
]


class FourOhFourResponse(object):
    __slots__ = ('body',
                 'doc_type',
                 'path',
                 'url',
                 'id')

    def __init__(self, http_response):
        self.body = get_clean_body(http_response)
        self.doc_type = http_response.doc_type
        self.path = http_response.get_url().get_domain_path().url_string
        self.url = http_response.get_url().url_string
        self.id = http_response.id

    def __repr__(self):
        return '<FourOhFourResponse (path:%s, body:"%s")>' % (self.path, self.body[:20])


class Decorator(object):
    def __get__(self, instance, instancetype):
        # https://stackoverflow.com/questions/5469956/python-decorator-self-is-mixed-up
        return functools.partial(self.__call__, instance)


class LRUCache404(Decorator):
    """
    This decorator caches the 404 responses to reduce CPU usage and,
    in some cases, HTTP requests being sent.
    """
    def __init__(self, _function):
        self._function = _function

        # It is OK to store 1000 here, I'm only storing path+filename as the
        # key, and bool as the value.
        self._is_404_LRU = SynchronizedLRUDict(1000)

    def __call__(self, *args, **kwargs):
        cache_key = self.get_cache_key(args)

        try:
            result = self._is_404_LRU[cache_key]
        except KeyError:
            result = self._function(*args, **kwargs)
            self._is_404_LRU[cache_key] = result
            return result
        else:
            return result

    def get_cache_key(self, args):
        http_response = args[1]
        return http_response.get_uri().url_string


class PreventMultipleThreads(Decorator):
    """
    This decorator tracks executions of is_404(), if one of those executions
    is running with parameter X, and new one call is made to is_404() with the
    same parameter, then the decorator forces the second caller to wait until
    the first execution is completed.

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
    TIMEOUT = 120

    def __init__(self, _function):
        self._function = _function
        self._404_call_events = {}

    def __call__(self, *args, **kwargs):
        call_key = self.get_call_key(args)

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
            wait_result = event.wait(timeout=self.TIMEOUT)
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
                msg = ('is_404() took more than %s seconds to run, returning'
                       ' True to reduce CPU usage and HTTP requests. This error'
                       ' is very rare and should be manually analyzed.')
                args = (self.TIMEOUT,)
                om.out.error(msg % args)
                return True
            else:
                # All right! is_404 function call is complete, now let's call
                # it again to obtain the result from the cache
                return self._function(*args, **kwargs)

    def get_call_key(self, args):
        http_response = args[1]
        return http_response.get_uri().url_string


class Fingerprint404(object):
    """
    Read the 404 page(s) returned by the server.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    _instance = None

    def __init__(self):
        #
        #   Set the opener, I need it to perform some tests and gain
        #   the knowledge about the server's 404 response bodies.
        #
        self._uri_opener = None
        self._worker_pool = None
        
        #
        #   Internal variables
        #
        self._already_analyzed = False
        self._lock = thread.allocate_lock()
        self._directory_uses_404_codes = ScalableBloomFilter()
        self._clean_404_response_db_calls = 0

        #
        #   There are two different 404 response databases, the base one is
        #   created during the scan initialization and will not be modified
        #   during the scan. The extended 404 DB is used during the scan to
        #   store new knowledge about the 404 responses which are captured.
        #
        self._base_404_responses = deque(maxlen=MAX_404_RESPONSES)
        self._extended_404_responses = deque(maxlen=MAX_404_RESPONSES)

    def cleanup(self):
        self._base_404_responses = None
        self._extended_404_responses = None
        self._already_analyzed = False
        self._directory_uses_404_codes = None
        self._clean_404_response_db_calls = 0

    def set_url_opener(self, urlopener):
        self._uri_opener = urlopener

    def set_worker_pool(self, worker_pool):
        self._worker_pool = worker_pool

    def generate_404_knowledge(self, url):
        """
        Based on a URL, request something that we know is going to be a 404.
        Afterwards analyze the 404's and summarise them.

        :return: A list with 404 bodies.
        """
        #
        #    This is the case when nobody has properly configured
        #    the object in order to use it.
        #
        if self._uri_opener is None:
            msg = ('404 fingerprint database was incorrectly initialized.'
                   ' URL opener is None.')
            raise RuntimeError(msg)

        # Get the filename extension and create a 404 for it
        extension = url.get_extension()
        domain_path = url.get_domain_path()

        #
        #   This is a list of the most common handlers, in some configurations,
        #   the 404 depends on the handler, so I want to make sure that I catch
        #   the 404 for each one
        #
        handlers = {'py', 'php', 'asp', 'aspx', 'do', 'jsp', 'rb', 'action',
                    'gif', 'htm', 'pl', 'cgi', 'xhtml', 'htmls', 'foobar'}
        if extension:
            handlers.add(extension)

        test_urls = []

        for handler_ext in handlers:
            rand_alnum_file = rand_alnum(8) + '.' + handler_ext
            url404 = domain_path.url_join(rand_alnum_file)
            test_urls.append(url404)

        # Also keep in mind that in some cases we don't have an extension, so
        # we need to create a URL with just a filename
        if not extension:
            rand_alnum_file = rand_alnum(8)
            url404 = domain_path.url_join(rand_alnum_file)
            test_urls.append(url404)

        imap_unordered = self._worker_pool.imap_unordered
        not_exist_resp_lst = []
        
        for not_exist_resp in imap_unordered(self._send_404, test_urls):
            four_oh_data = FourOhFourResponse(not_exist_resp)
            not_exist_resp_lst.append(four_oh_data)

            #
            # Populate the self._directory_uses_404_codes with the information
            # we just retrieved from the application
            #
            if not_exist_resp.get_code() == 404:

                url_404 = not_exist_resp.get_uri()

                path_extension = (url_404.get_domain_path(),
                                  url_404.get_extension())

                # No need to check if the ScalableBloomFilter contains the key
                # It is a "set", adding duplicates is a no-op.
                self._directory_uses_404_codes.add(path_extension)

        #
        # Sort the HTTP responses by length to try to have the same DB on
        # each call to generate_404_knowledge(). This is required because of
        # the imap_unordered() above, which will yield the responses in
        # unexpected order each time we call it.
        #
        def sort_by_response_length(a, b):
            return cmp(len(a.body), len(b.body))

        not_exist_resp_lst.sort(sort_by_response_length)

        #
        # I have the 404 responses in not_exist_resp_lst, but maybe they
        # all look the same, so I'll filter the ones that look alike.
        #
        # Just add the first one to the 404 responses list, since that one is
        # "unique"
        #
        if len(not_exist_resp_lst):
            four_oh_data = not_exist_resp_lst[0]
            self._append_to_base_404_responses(four_oh_data)

        # And now add the unique responses
        for i in not_exist_resp_lst:
            for j in self._base_404_responses:

                if i is j:
                    break

                if fuzzy_equal(i.body, j.body, IS_EQUAL_RATIO):
                    # i (or something really similar) already exists in the
                    # self._base_404_responses, no need to compare any further
                    break
            else:
                # None of the 404_responses match the item from not_exist_resp_lst
                # This means that this item is new and we should store it in the
                # 404_responses db
                self._append_to_base_404_responses(i)

        msg = 'The base 404 response DB contains responses with IDs: %s'
        args = (', '.join(str(r.id) for r in copy.copy(self._base_404_responses)))
        om.out.debug(msg % args)

    def _append_to_base_404_responses(self, data):
        self._base_404_responses.append(data)

        msg = ('Added 404 data for "%s" (id:%s, len:%s) to the base'
               ' 404 result database (size: %s/%s)')
        args = (data.url,
                data.id,
                len(data.body),
                len(self._base_404_responses),
                MAX_404_RESPONSES)
        om.out.debug(msg % args)

    def _append_to_extended_404_responses(self, data):
        self._extended_404_responses.append(data)

        msg = ('Added 404 data for "%s" (id:%s, len:%s)) to the extended'
               ' 404 result database (size: %s/%s)')
        args = (data.url,
                data.id,
                len(data.body),
                len(self._base_404_responses),
                MAX_404_RESPONSES)
        om.out.debug(msg % args)

        self.clean_404_response_db()

    def get_404_responses(self):
        all_404 = itertools.chain(copy.copy(self._base_404_responses),
                                  copy.copy(self._extended_404_responses))

        for resp_404 in all_404:
            yield resp_404

    def clean_404_response_db(self):
        """
        During the scan, and because I chose to remove the very broad 404
        database lock, the 404 response database might become untidy: the same
        HTTP response might be appended to the DB multiple times.

        An untidy DB triggers more comparisons between HTTP responses, which
        is CPU-intensive.

        This method cleans the DB every N calls to reduce any duplicates.

        :return: None. The extended DB is modified.
        """
        self._clean_404_response_db_calls += 1

        if self._clean_404_response_db_calls % CLEAN_DB_EVERY != 0:
            return

        removed_items = 0
        extended_404_response_copy = copy.copy(self._extended_404_responses)

        for i in extended_404_response_copy:
            for j in extended_404_response_copy:

                if i is j:
                    continue

                if not fuzzy_equal(i.body, j.body, IS_EQUAL_RATIO):
                    continue

                # i (or something really similar) already exists in
                # self._extended_404_responses, no need to compare any further
                # just remove it and continue with the next
                try:
                    self._extended_404_responses.remove(i)
                except ValueError:
                    # The 404 response DB might have been changed by another thread
                    break
                else:
                    msg = ('Removed 404 response for "%s" (id: %s) from the 404 DB'
                           ' because it matches 404 response "%s" (id: %s)')
                    args = (i.url, i.id, j.url, j.id)
                    om.out.debug(msg % args)

                    removed_items += 1

                    break

        msg = 'Called clean 404 response DB. Removed %s duplicates from DB.'
        args = (removed_items,)
        om.out.debug(msg % args)

        msg = 'The extended 404 response DB contains responses with IDs: %s'
        args = (', '.join(str(r.id) for r in copy.copy(self._extended_404_responses)))
        om.out.debug(msg % args)

    @retry(tries=2, delay=0.5, backoff=2)
    def _send_404(self, url404, debugging_id=None):
        """
        Sends a GET request to url404.

        :return: The HTTP response body.
        """
        # I don't use the cache, because the URLs are random and the only thing
        # that cache does is to fill up disk space
        try:
            response = self._uri_opener.GET(url404,
                                            cache=False,
                                            grep=False,
                                            debugging_id=debugging_id)
        except HTTPRequestException, hre:
            message = 'Exception found while detecting 404: "%s"'
            om.out.debug(message % hre)
            raise FourOhFourDetectionException(message % hre)

        return response

    @PreventMultipleThreads
    @LRUCache404
    def is_404(self, http_response):
        """
        All of my previous versions of is_404 were very complex and tried to
        struggle with all possible cases. The truth is that in most "strange"
        cases I was failing miserably, so now I changed my 404 detection once
        again, but keeping it as simple as possible.

        Also, and because I was trying to cover ALL CASES, I was performing a
        lot of requests in order to cover them, which in most situations was
        unnecessary.

        So now I go for a much simple approach:
            1- Cover the simplest case of all using only 1 HTTP request
            2- Give the users the power to configure the 404 detection by
               setting a string that identifies the 404 response (in case we
               are missing it for some reason in case #1)

        :param http_response: The HTTP response which we want to know if it
                                  is a 404 or not.
        """
        domain_path = http_response.get_url().get_domain_path()
        extension = http_response.get_url().get_extension()

        #
        #   First we handle the user configured exceptions:
        #
        if domain_path in cf.cf.get('always_404'):
            return True

        if domain_path in cf.cf.get('never_404'):
            return False

        #
        #    The user configured setting. "If this string is in the response,
        #    then it is a 404"
        #
        if cf.cf.get('string_match_404') and cf.cf.get('string_match_404') in http_response:
            return True

        #
        #   This is the most simple case, we don't even have to think about this
        #
        #   If there is some custom website that always returns 404 codes, then
        #   we are screwed, but this is open source, and the pentester working
        #   on that site can modify these lines.
        #
        if http_response.get_code() == 404:
            return True

        #
        #   This is an edge case. Let me explain...
        #
        #   Doing try/except in all plugins that send HTTP requests was hard (tm)
        #   so plugins don't use ExtendedUrllib directly, instead they use the
        #   UrlOpenerProxy (defined in plugin.py). This proxy catches any
        #   exceptions and returns a 204 response.
        #
        #   In most cases that works perfectly, because it will allow the plugin
        #   to keep working without caring much about the exceptions. In some
        #   edge cases someone will call is_404(204_response_generated_by_w3af)
        #   and that will most likely return False, because the 204 response we
        #   generate doesn't look like anything w3af has in the 404 DB.
        #
        #   The following iff fixes the race condition
        #
        if http_response.get_code() == 204:
            if http_response.get_msg() == NO_CONTENT_MSG:
                if http_response.get_headers() == Headers():
                    return True

        #
        #   Lets start with the rather complex code...
        #
        with self._lock:
            if not self._already_analyzed:
                self.generate_404_knowledge(http_response.get_url())
                self._already_analyzed = True

        #
        #    Simple, if the file we requested is in a directory that's known to
        #    return 404 codes for files that do not exist, AND this is NOT a 404
        #    then we're return False!
        #
        path_extension = (domain_path, extension)
        if path_extension in self._directory_uses_404_codes:
            if http_response.get_code() != 404:
                return False

        # 404_body stored in the DB was already cleaned inside
        # generate_404_knowledge
        #
        # We need to clean the body we receive as parameter in order to have
        # a fair comparison
        resp_body = get_clean_body(http_response)
        resp_content_type = http_response.doc_type
        resp_path = http_response.get_url().get_domain_path().url_string

        # See https://github.com/andresriancho/w3af/issues/6646
        max_similarity_with_404 = 0.0
        resp_path_in_db = False
        debugging_id = rand_alnum(8)

        #
        #   Compare this response to all the 404's I have in my DB
        #
        for resp_404 in self.get_404_responses():

            # Since the fuzzy_equal function is CPU-intensive we want to
            # avoid calling it for cases where we know it won't match, for
            # example in comparing an image and an html
            if resp_content_type != resp_404.doc_type:
                continue

            is_fuzzy_equal, distance = fuzzy_equal_return_distance(resp_404.body,
                                                                   resp_body,
                                                                   IS_EQUAL_RATIO)

            if is_fuzzy_equal:
                msg = ('"%s" (id:%s, code:%s, len:%s, did:%s) is a 404'
                       ' [similarity_index > %s with 404 DB entry with ID %s]')
                args = (http_response.get_url(),
                        http_response.id,
                        http_response.get_code(),
                        len(http_response.get_body()),
                        debugging_id,
                        IS_EQUAL_RATIO,
                        resp_404.id)
                om.out.debug(msg % args)
                return True

            if distance is None:
                distance = 0.0

                # In some cases the distance is None, because the
                # fuzzy_equal didn't have to calculate it to produce the result
                # (because of the optimizations)
                #
                # Also, we can calculate the upper_bound_similarity which
                # indicates how much (in the best case) two strings can look
                # alike based on their lengths
                #
                # This allows us to calculate the distance between two strings
                # only if we know that the distance could be large enough
                ups = upper_bound_similarity(len(resp_404.body), len(resp_body))

                if ups > max_similarity_with_404:
                    distance = relative_distance(resp_404.body, resp_body)

            max_similarity_with_404 = max(max_similarity_with_404, distance)

            # Track if the response path is in the DB
            if not resp_path_in_db and resp_path == resp_404.path:
                resp_path_in_db = True

        #
        # I get here when the for ends and no 404 body matched with
        # the resp_body that was sent as a parameter. This means one of two things:
        #
        #     * There is not enough knowledge in get_404_responses(), or
        #
        #     * The answer is NOT a 404.
        #
        # Because we want to reduce the amount of false positives that
        # this method returns, we'll perform some extra checks before
        # saying that this is NOT a 404.
        #
        if resp_path_in_db and max_similarity_with_404 < MUST_VERIFY_RATIO:
            msg = ('"%s" (id:%s, code:%s, len:%s, did:%s) is NOT a 404'
                   ' [similarity_index < %s with sample path in 404 DB]')
            args = (http_response.get_url(),
                    http_response.id,
                    http_response.get_code(),
                    len(http_response.get_body()),
                    debugging_id,
                    MUST_VERIFY_RATIO)
            om.out.debug(msg % args)
            return False

        if self._is_404_with_extra_request(http_response, resp_body, debugging_id):
            #
            #   Aha! It is a 404!
            #
            msg = ('"%s" (id:%s, code:%s, len:%s, did:%s) is a 404'
                   ' [similarity_index > %s with extra request]')
            args = (http_response.get_url(),
                    http_response.id,
                    http_response.get_code(),
                    len(http_response.get_body()),
                    debugging_id,
                    IS_EQUAL_RATIO)
            om.out.debug(msg % args)
            return True

        msg = '"%s" (id:%s, code:%s, len:%s, did:%s) is NOT a 404 [default to False]'
        args = (http_response.get_url(),
                http_response.id,
                http_response.get_code(),
                len(http_response.get_body()),
                debugging_id)
        om.out.debug(msg % args)

        return False

    def _is_404_with_extra_request(self, http_response, clean_resp_body, debugging_id):
        """
        Performs a very simple check to verify if this response is a 404 or not.

        It takes the original URL and modifies it by flipping some bytes in the
        filename, then performs a request to that URL and compares the original
        response with the modified one. If they are equal then the original
        request is a 404.

        :param http_response: The original HTTP response
        :param clean_resp_body: The original HTML body you could find in
                                http_response after passing it by a cleaner

        :return: True if the original response was a 404 !
        """
        #
        #   Generate a request that will trigger a 404
        #
        response_url = http_response.get_url()
        filename = response_url.get_file_name()

        if not filename:
            relative_url = '../%s/' % rand_alnum(8)
            url_404 = response_url.url_join(relative_url)
        else:
            relative_url = generate_404_filename(filename)
            url_404 = response_url.copy()
            url_404.set_file_name(relative_url)

        #
        #   Send the 404 request
        #
        response_404 = self._send_404(url_404, debugging_id=debugging_id)
        four_oh_data = FourOhFourResponse(response_404)

        #
        #   Update _directory_uses_404_codes
        #
        if response_404.get_code() == 404:
            path_extension = (url_404.get_domain_path(),
                              url_404.get_extension())

            self._directory_uses_404_codes.add(path_extension)
            self._append_to_extended_404_responses(four_oh_data)

            if http_response.get_code() != 404:
                # Not a 404! We know because of the new knowledge that this path
                # and extension uses 404
                msg = ('The generated HTTP response for %s (id: %s) has a 404'
                       ' code, which is different from code %s used by the HTTP'
                       ' response passed as parameter (id:%s, did:%s)')
                args = (url_404,
                        response_404.id,
                        http_response.get_code(),
                        http_response.id,
                        debugging_id)
                om.out.debug(msg % args)
                return False

        #
        #   If the HTTP response codes are different, then we're almost certain
        #   the HTTP response received as parameter is not a 404
        #
        if response_404.get_code() != http_response.get_code():
            msg = ('The generated HTTP response for %s (id: %s) has a %s'
                   ' code, which is different from code %s used by the HTTP'
                   ' response passed as parameter (id:%s, did:%s)')
            args = (url_404,
                    response_404.id,
                    response_404.get_code(),
                    http_response.get_code(),
                    http_response.id,
                    debugging_id)
            om.out.debug(msg % args)

            #
            #   Save the new 404 page to the DB. This might prevent us from
            #   sending extra HTTP requests in the future
            #
            self._append_to_extended_404_responses(four_oh_data)

            return False

        #
        #   Compare the "response that MUST BE (*) a 404" with the one
        #   received as parameter.
        #
        #   (*) This works in 95% of the cases, where the application is not
        #       using some kind of URL rewrite rule which completely ignores
        #       the last part of the URL (filename or path)
        #
        is_fuzzy_equal = fuzzy_equal(four_oh_data.body,
                                     clean_resp_body,
                                     IS_EQUAL_RATIO)

        #
        #   Not equal! This means that the URL we generated really triggered
        #   a 404, and that the response received as parameter is different
        #   (not a 404)
        #
        if not is_fuzzy_equal:
            msg = ('The generated HTTP response for %s (id: %s) is different'
                   ' from the HTTP response body passed as parameter'
                   ' (id: %s, did:%s)')
            args = (url_404,
                    four_oh_data.id,
                    http_response.id,
                    debugging_id)
            om.out.debug(msg % args)

            #
            #   Save the new 404 page to the DB. This might prevent us from
            #   sending extra HTTP requests in the future
            #
            self._append_to_extended_404_responses(four_oh_data)

            return False

        #
        #   The responses are fuzzy-equal, both can be 404, or both can be the
        #   result of the application ignoring the last part of the URL,
        #   example:
        #
        #       http://w3af.com/foo/ignored
        #       http://w3af.com/foo/also-ignored
        #
        if self._looks_like_404_page(http_response):
            msg = ('The HTTP response passed as parameter (id: %s) looks like'
                   ' a 404 response AND is similar to the generated HTTP 404'
                   ' response (id:%s, url:%s) (did:%s)')
            args = (http_response.id,
                    four_oh_data.id,
                    url_404,
                    debugging_id)
            om.out.debug(msg % args)

            #
            #   Save the new 404 page to the DB. This might prevent us from
            #   sending extra HTTP requests in the future
            #
            self._append_to_extended_404_responses(four_oh_data)

            return True

        #
        #   This is the worse scenario. The responses are equal, none of the
        #   responses look like a 404. We get here when:
        #
        #       * _looks_like_404_page() has a false negative (the page is a 404,
        #         but the method returns False, this is very common, since the
        #         word database is very small)
        #
        #       * The site is ignoring the last part of the URL (the filename or
        #         the last path). So requesting /abc/def and /abc/foo will both
        #         yield the same result.
        #
        #   There is no good answer here... I prefer to return False, which
        #   might add a false positive finding to the KB, instead of returning
        #   True (saying that the response is a 404) and having a false negative
        #
        msg = ('The generated HTTP response for %s (id: %s) is very similar to'
               ' the HTTP response body passed as parameter (id: %s), and the'
               ' generated response does NOT look like a 404 (did:%s)')
        args = (url_404,
                four_oh_data.id,
                http_response.id,
                debugging_id)
        om.out.debug(msg % args)
        return False

    def _looks_like_404_page(self, response_404):
        """
        Match some very common 404 strings against the response, each matching
        string increases the score. If the score is greater than MIN_SCORE_FOR_404
        then this method returns True.

        Use with care, this method will yield a lot of false positives and
        should only be used as part of the decision making process.

        Want to improve this method? Maybe use machine learning!

            https://github.com/andresriancho/w3af/issues/17171

        :param response_404: HTTPResponse instance which we want to know
                             if it looks like a 404 or not.
        :return: Boolean indicating if the response looks like a 404
        """
        # This will capture 404, 403, 401, 500, etc. Anything that looks ugly
        if response_404.get_code() in range(400, 600):
            return True

        score = 0
        lower_404_body = response_404.get_body().lower()

        already_found = set()

        for word in COMMON_404_WORDS:
            if word in lower_404_body and word not in already_found:
                score += 1
                already_found.add(word)

        return score >= MIN_SCORE_FOR_404


def fingerprint_404_singleton(cleanup=False):
    if Fingerprint404._instance is None or cleanup:
        Fingerprint404._instance = Fingerprint404()

    return Fingerprint404._instance


#
#
#       Some helper functions
#
#
def is_404(http_response):
    #    Get an instance of the 404 database
    fp_404_db = fingerprint_404_singleton()
    return fp_404_db.is_404(http_response)


def get_clean_body(response):
    """
    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/
            - response.get_body() == 'spam aaaaaaa eggs'

        - output:
            - self._clean_body( response ) == 'spam  eggs'

    The same works with file names.
    All of them, are removed url-decoded and "as is".

    :param response: The HTTPResponse object to clean
    :return: A string that represents the "cleaned" response body of the
             response.
    """
    body = response.body

    if not response.is_text_or_html():
        return body

    # Do some real work...
    base_urls = [response.get_url(),
                 response.get_url().switch_protocol(),
                 response.get_uri(),
                 response.get_uri().switch_protocol()]

    to_replace = []
    for base_url in base_urls:
        to_replace.extend([u.url_string for u in base_url.get_directories()])
        to_replace.extend(base_url.url_string.split(u'/'))
        to_replace.extend([base_url.url_string,
                           base_url.all_but_scheme(),
                           base_url.get_path_qs(),
                           base_url.get_path()])

    # Filter some strings
    to_replace = [trs for trs in to_replace if len(trs) > 6]
    to_replace = list(set(to_replace))

    return get_clean_body_impl(response, to_replace, multi_encode=False)

