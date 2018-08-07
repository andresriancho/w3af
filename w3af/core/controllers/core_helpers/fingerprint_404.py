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
import itertools

from functools import wraps
from collections import deque

# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.url.helpers import get_clean_body_impl

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


class FourOhFourResponse(object):
    __slots__ = ('body',
                 'doc_type',
                 'path')

    def __init__(self, http_response):
        self.body = get_clean_body(http_response)
        self.doc_type = http_response.doc_type
        self.path = http_response.get_url().get_domain_path().url_string


def lru_404_cache(wrapped_method):

    @wraps(wrapped_method)
    def inner(self, http_response):
        path = http_response.get_uri().url_string

        try:
            return self.is_404_LRU[path]
        except KeyError:
            result = wrapped_method(self, http_response)
            self.is_404_LRU[path] = result
            return result

    return inner


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

        # It is OK to store 1000 here, I'm only storing path+filename as the key,
        # and bool as the value.
        self.is_404_LRU = SynchronizedLRUDict(1000)

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

    def _append_to_base_404_responses(self, data):
        self._base_404_responses.append(data)

        if len(self._base_404_responses) >= MAX_404_RESPONSES:
            msg_fmt = 'The base 404 body result database has reached MAX_404_RESPONSES!'
            om.out.debug(msg_fmt)
        else:
            msg_fmt = 'The base 404 body result database has a length of %s.'
            om.out.debug(msg_fmt % len(self._base_404_responses))

    def _append_to_extended_404_responses(self, data):
        self._extended_404_responses.append(data)

        if len(self._extended_404_responses) >= MAX_404_RESPONSES:
            msg_fmt = 'The extended 404 body result database has reached MAX_404_RESPONSES!'
            om.out.debug(msg_fmt)
        else:
            msg_fmt = 'The extended 404 body result database has a length of %s.'
            om.out.debug(msg_fmt % len(self._extended_404_responses))

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

        items_to_remove = []
        extended_404_response_copy = copy.copy(self._extended_404_responses)

        for i in extended_404_response_copy:
            for j in extended_404_response_copy:

                if i is j:
                    continue

                if fuzzy_equal(i.body, j.body, IS_EQUAL_RATIO):
                    # i (or something really similar) already exists in the
                    # self._extended_404_responses, no need to compare any further
                    items_to_remove.append(i)
                    break

        for i in items_to_remove:
            try:
                self._extended_404_responses.remove(i)
            except ValueError:
                # The 404 response DB might have been changed by another thread
                continue

        msg = 'Called clean 404 response DB. Removed %s duplicates from DB.'
        args = (len(items_to_remove),)
        om.out.debug(msg % args)

    @retry(tries=2, delay=0.5, backoff=2)
    def _send_404(self, url404):
        """
        Sends a GET request to url404.

        :return: The HTTP response body.
        """
        # I don't use the cache, because the URLs are random and the only thing
        # that cache does is to fill up disk space
        try:
            response = self._uri_opener.GET(url404, cache=False, grep=False)
        except HTTPRequestException, hre:
            message = 'Exception found while detecting 404: "%s"'
            raise FourOhFourDetectionException(message % hre)

        return response

    @lru_404_cache
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
                msg = '"%s" (id:%s) is a 404 [similarity_index > %s]'
                fmt = (http_response.get_url(),
                       http_response.id,
                       IS_EQUAL_RATIO)
                om.out.debug(msg % fmt)
                return True
            else:
                current_ratio = 0.0

                if distance is None:
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
                        current_ratio = relative_distance(resp_404.body, resp_body)
                else:
                    current_ratio = distance

                max_similarity_with_404 = max(max_similarity_with_404,
                                              current_ratio)

            # Track if the response path is in the DB
            if not resp_path_in_db and resp_path == resp_404.path:
                resp_path_in_db = True

        #
        # I get here when the for ends and no body_404_db matched with
        # the resp_body that was sent as a parameter by the user. This
        # means one of two things:
        #
        #     * There is not enough knowledge in self._404_responses, or
        #
        #     * The answer is NOT a 404.
        #
        # Because we want to reduce the amount of "false positives" that
        # this method returns, we'll perform some extra checks before
        # saying that this is NOT a 404.
        #
        if resp_path_in_db and max_similarity_with_404 < MUST_VERIFY_RATIO:
            msg = ('"%s" (id:%s) is NOT a 404 [similarity_index < %s'
                   ' with sample path in 404 DB].')
            args = (http_response.get_url(),
                    http_response.id,
                    MUST_VERIFY_RATIO)
            om.out.debug(msg % args)
            return False

        if self._is_404_with_extra_request(http_response, resp_body):
            #
            #   Aha! It is a 404!
            #
            msg = '"%s" (id:%s) is a 404, used extra request [similarity_index > %s].'
            fmt = (http_response.get_url(), http_response.id, IS_EQUAL_RATIO)
            om.out.debug(msg % fmt)
            return True

        msg = '"%s" (id:%s) is NOT a 404 [similarity_index < %s].'
        args = (http_response.get_url(), http_response.id, IS_EQUAL_RATIO)
        om.out.debug(msg % args)

        return False

    def _is_404_with_extra_request(self, http_response, clean_resp_body):
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
        response_404 = self._send_404(url_404)

        #
        #   Update _directory_uses_404_codes
        #
        if response_404.get_code() == 404:
            path_extension = (url_404.get_domain_path(),
                              url_404.get_extension())

            self._directory_uses_404_codes.add(path_extension)

            if http_response.get_code() != 404:
                # Not a 404! We know because of the new knowledge that this path
                # and extension uses 404
                return False

        #
        #   Compare the "response that MUST BE (*) a 404" with the one
        #   received as parameter.
        #
        #   (*) This works in 95% of the cases, where the application is not
        #       using some kind of URL rewrite rule which completely ignores
        #       the last part of the URL (filename or path)
        #
        four_oh_data = FourOhFourResponse(response_404)
        self._append_to_extended_404_responses(four_oh_data)

        return fuzzy_equal(four_oh_data.body,
                           clean_resp_body,
                           IS_EQUAL_RATIO)


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

