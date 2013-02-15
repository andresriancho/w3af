'''
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

'''
from __future__ import with_statement

import cgi
import thread
import urllib

import core.data.kb.config as cf
import core.controllers.output_manager as om

from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.data.fuzzer.utils import rand_alnum

from core.controllers.misc.levenshtein import relative_distance_ge
from core.controllers.misc.lru import LRU
from core.controllers.misc.decorators import retry


IS_EQUAL_RATIO = 0.90


class fingerprint_404(object):
    '''
    Read the 404 page(s) returned by the server.

    :author: Andres Riancho (andres.riancho@gmail.com)
    '''

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
        self._404_bodies = []
        self._lock = thread.allocate_lock()
        self._fingerprinted_paths = ScalableBloomFilter()
        self._directory_uses_404_codes = ScalableBloomFilter()

        # It is OK to store 200 here, I'm only storing path+filename as the key,
        # and bool as the value.
        self.is_404_LRU = LRU(200)

    def set_url_opener(self, urlopener):
        self._uri_opener = urlopener

    def set_worker_pool(self, worker_pool):
        self._worker_pool = worker_pool

    def generate_404_knowledge(self, url):
        '''
        Based on a URL, request something that we know is going to be a 404.
        Afterwards analyze the 404's and summarise them.

        :return: A list with 404 bodies.
        '''
        #
        #    This is the case when nobody has properly configured
        #    the object in order to use it.
        #
        if self._uri_opener is None:
            msg = '404 fingerprint database was incorrectly initialized.'
            raise RuntimeError(msg)

        # Get the filename extension and create a 404 for it
        extension = url.get_extension()
        domain_path = url.get_domain_path()

        # the result
        self._response_body_list = []

        #
        #   This is a list of the most common handlers, in some configurations, the 404
        #   depends on the handler, so I want to make sure that I catch the 404 for each one
        #
        handlers = set()
        handlers.update(
            ['py', 'php', 'asp', 'aspx', 'do', 'jsp', 'rb', 'do'])
        handlers.update(
            ['gif', 'htm', 'pl', 'cgi', 'xhtml', 'htmls', 'foobar'])
        if extension:
            handlers.add(extension)

        args_list = []

        for extension in handlers:
            rand_alnum_file = rand_alnum(8) + '.' + extension
            url404 = domain_path.url_join(rand_alnum_file)
            args_list.append(url404)

        self._worker_pool.map(self._send_404, args_list)

        #
        #   I have the bodies in self._response_body_list , but maybe they
        #   all look the same, so I'll filter the ones that look alike.
        #
        result = [self._response_body_list[0], ]
        for i in self._response_body_list:
            for j in self._response_body_list:

                if relative_distance_ge(i, j, IS_EQUAL_RATIO):
                    # They are equal, we are ok with that
                    continue
                else:
                    # They are no equal, this means that we'll have to add this to the list
                    result.append(j)

        # I don't need these anymore
        self._response_body_list = None

        # And I return the ones I need
        result = list(set(result))
        om.out.debug('The 404 body result database has a length of ' +
                     str(len(result)) + '.')

        self._404_bodies = result
        self._already_analyzed = True
        self._fingerprinted_paths.add(domain_path)

    def need_analysis(self):
        return not self._already_analyzed

    @retry(tries=2, delay=0.5, backoff=2)
    def _send_404(self, url404, store=True):
        '''
        Sends a GET request to url404 and saves the response in self._response_body_list .
        :return: The HTTP response body.
        '''
        # I don't use the cache, because the URLs are random and the only thing that
        # cache does is to fill up disk space
        response = self._uri_opener.GET(url404, cache=False, grep=False)

        if store:
            # I don't want the random file name to affect the 404, so I replace
            # it with a blank space,
            response_body = get_clean_body(response)
            self._response_body_list.append(response_body)

        return response

    def is_404(self, http_response):
        '''
        All of my previous versions of is_404 were very complex and tried to
        struggle with all possible cases. The truth is that in most "strange"
        cases I was failing miserably, so now I changed my 404 detection once
        again, but keeping it as simple as possible.

        Also, and because I was trying to cover ALL CASES, I was performing a
        lot of requests in order to cover them, which in most situations was
        unnecesary.

        So now I go for a much simple approach:
            1- Cover the simplest case of all using only 1 HTTP request
            2- Give the users the power to configure the 404 detection by
               setting a string that identifies the 404 response (in case we
               are missing it for some reason in case #1)

        :param http_response: The HTTP response which we want to know if it
                                  is a 404 or not.
        '''
        #
        #   First we handle the user configured exceptions:
        #
        domain_path = http_response.get_url().get_domain_path()
        if domain_path in cf.cf.get('always_404'):
            return True
        elif domain_path in cf.cf.get('never_404'):
            return False

        #
        #    The user configured setting. "If this string is in the response,
        #    then it is a 404"
        #
        if cf.cf.get('string_match_404') and cf.cf.get('string_match_404') in http_response:
            return True

        #
        #   This is the most simple case, we don't even have to think about this.
        #
        #   If there is some custom website that always returns 404 codes, then we
        #   are screwed, but this is open source, and the pentester working on
        #   that site can modify these lines.
        #
        if http_response.get_code() == 404:
            return True

        #
        #    Simple, if the file we requested is in a directory that's known to
        #    return 404 codes for files that do not exist, AND this is NOT a 404
        #    then we're return False!
        #
        if domain_path in self._directory_uses_404_codes and \
                http_response.get_code() != 404:
            return False

        #
        #   Before actually working, I'll check if this response is in the LRU,
        #   if it is I just return the value stored there.
        #
        if http_response.get_url().get_path() in self.is_404_LRU:
            return self.is_404_LRU[http_response.get_url().get_path()]

        with self._lock:
            if self.need_analysis():
                self.generate_404_knowledge(http_response.get_url())

        # self._404_body was already cleaned inside generate_404_knowledge
        # so we need to clean this one in order to have a fair comparison
        html_body = get_clean_body(http_response)

        #
        #    Compare this response to all the 404's I have in my DB
        #
        #    Note: while self._404_bodies is a list, we can perform this for loop
        #          without "with self._lock", read comments in stackoverflow:
        #          http://stackoverflow.com/questions/9515364/does-python-freeze-the-list-before-for-loop
        #
        for body_404_db in self._404_bodies:

            if relative_distance_ge(body_404_db, html_body, IS_EQUAL_RATIO):
                msg = '"%s" (id:%s) is a 404 [similarity_index > %s]'
                fmt = (
                    http_response.get_url(), http_response.id, IS_EQUAL_RATIO)
                om.out.debug(msg % fmt)
                return self._fingerprinted_as_404(http_response)

        else:
            #
            #    I get here when the for ends and no body_404_db matched with the
            #    html_body that was sent as a parameter by the user. This means one
            #    of two things:
            #        * There is not enough knowledge in self._404_bodies, or
            #        * The answer is NOT a 404.
            #
            #    Because we want to reduce the amount of "false positives" that
            #    this method returns, we'll perform one extra check before saying
            #    that this is NOT a 404.
            if http_response.get_url().get_domain_path() not in self._fingerprinted_paths:
                if self._single_404_check(http_response, html_body):
                    self._404_bodies.append(html_body)
                    self._fingerprinted_paths.add(
                        http_response.get_url().get_domain_path())

                    msg = '"%s" (id:%s) is a 404 (similarity_index > %s). Adding new'
                    msg += ' knowledge to the 404_bodies database (length=%s).'
                    fmt = (http_response.get_url(), http_response.id,
                           IS_EQUAL_RATIO, len(self._404_bodies))
                    om.out.debug(msg % fmt)

                    return self._fingerprinted_as_404(http_response)

            msg = '"%s" (id:%s) is NOT a 404 [similarity_index < %s].'
            fmt = (http_response.get_url(), http_response.id, IS_EQUAL_RATIO)
            om.out.debug(msg % fmt)
            return self._fingerprinted_as_200(http_response)

    def _fingerprinted_as_404(self, http_response):
        '''
        Convenience function so that I don't forget to update the LRU
        :return: True
        '''
        self.is_404_LRU[http_response.get_url().get_path()] = True
        return True

    def _fingerprinted_as_200(self, http_response):
        '''
        Convenience function so that I don't forget to update the LRU
        :return: False
        '''
        self.is_404_LRU[http_response.get_url().get_path()] = False
        return False

    def _single_404_check(self, http_response, html_body):
        '''
        Performs a very simple check to verify if this response is a 404 or not.

        It takes the original URL and modifies it by pre-pending a "not-" to the
        filename, then performs a request to that URL and compares the original
        response with the modified one. If they are equal then the original
        request is a 404.

        :param http_response: The original HTTP response
        :param html_body: The original HTML body after passing it by a cleaner

        :return: True if the original response was a 404 !
        '''
        response_url = http_response.get_url()
        filename = response_url.get_file_name()
        if not filename:
            relative_url = '../%s/' % rand_alnum(8)
            url_404 = response_url.url_join(relative_url)
        else:
            relative_url = 'not-%s' % filename
            url_404 = response_url.url_join(relative_url)

        response_404 = self._send_404(url_404, store=False)
        clean_response_404_body = get_clean_body(response_404)

        if response_404.get_code() == 404 and \
                url_404.get_domain_path() not in self._directory_uses_404_codes:
            self._directory_uses_404_codes.add(url_404.get_domain_path())

        return relative_distance_ge(clean_response_404_body, html_body, IS_EQUAL_RATIO)


def fingerprint_404_singleton(cleanup=False):
    if fingerprint_404._instance is None or cleanup:
        fingerprint_404._instance = fingerprint_404()

    return fingerprint_404._instance


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
    '''
    @see: blind_sqli_response_diff.get_clean_body()

    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/
            - response.get_body() == 'spam aaaaaaa eggs'

        - output:
            - self._clean_body( response ) == 'spam  eggs'

    The same works with filenames.
    All of them, are removed encoded and "as is".

    :param response: The HTTPResponse object to clean
    :return: A string that represents the "cleaned" response body of the response.
    '''

    body = response.body

    if response.is_text_or_html():
        url = response.get_url()
        to_replace = url.url_string.split('/')
        to_replace.append(url.url_string)

        for repl in to_replace:
            if len(repl) > 6:
                body = body.replace(repl, '')
                body = body.replace(urllib.unquote_plus(repl), '')
                body = body.replace(cgi.escape(repl), '')
                body = body.replace(cgi.escape(urllib.unquote_plus(repl)), '')

    return body
