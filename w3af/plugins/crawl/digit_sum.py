"""
digit_sum.py

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
import re
import copy

from itertools import izip, repeat

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_not_equal
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.dc.headers import Headers


DIGIT_REGEX = re.compile(r'(\d+)')


class digit_sum(CrawlPlugin):
    """
    Take an URL with a number (index2.asp) and try to find related files
    (index1.asp, index3.asp).

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)
        self._already_visited = ScalableBloomFilter()

        # User options
        self._fuzz_images = False
        self._max_digit_sections = 4

    def crawl(self, fuzzable_request, debugging_id):
        """
        Searches for new URLs by adding and subtracting numbers to the file
        and the parameters.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        """
        # If the fuzzable request sends post-data in any way, we don't want to
        # start fuzzing the URL, it simply doesn't make any sense.
        if fuzzable_request.get_data() or fuzzable_request.get_method() != 'GET':
            return

        url = fuzzable_request.get_url()

        headers = Headers([('Referer', url.url_string)])
        fuzzable_request.get_headers().update(headers)

        original_response = self._uri_opener.send_mutant(fuzzable_request,
                                                         cache=True)

        if original_response.is_text_or_html() or self._fuzz_images:

            fr_generator = self._mangle_digits(fuzzable_request)
            response_repeater = repeat(original_response)

            args = izip(fr_generator, response_repeater)

            self.worker_pool.map_multi_args(self._do_request, args)

            # I add myself so the next call to this plugin wont find me ...
            # Example: index1.html ---> index2.html --!!--> index1.html
            self._already_visited.add(fuzzable_request.get_uri())

    def _do_request(self, fuzzable_request, original_resp):
        """
        Send the request.

        :param fuzzable_request: The modified fuzzable request
        :param original_resp: The response for the original request that was
                              sent.
        """
        response = self._uri_opener.send_mutant(fuzzable_request, cache=True)

        if is_404(response):
            return

        # We have different cases:
        #    - If the URLs are different, then there is nothing to think
        #      about, we simply found something new!
        if response.get_url() != original_resp.get_url():
            self.output_queue.put(fuzzable_request)

        #    - If the content type changed, then there is no doubt that
        #      we've found something new!
        elif response.doc_type != original_resp.doc_type:
            self.output_queue.put(fuzzable_request)

        #    - If we changed the query string parameters, we have to check
        #      the content
        elif fuzzy_not_equal(response.get_clear_text_body(),
                             original_resp.get_clear_text_body(), 0.8):
            # In this case what might happen is that the number we changed
            # is "out of range" and when requesting that it will trigger an
            # error in the web application, or show us a non-interesting
            # response that holds no content.
            #
            # We choose to return these to the core because they might help
            # with the code coverage efforts. Think about something like:
            #     foo.aspx?id=OUT_OF_RANGE&foo=inject_here
            # vs.
            #     foo.aspx?id=IN_RANGE&foo=inject_here
            #
            # This relates to the EXPECTED_URLS in test_digit_sum.py
            self.output_queue.put(fuzzable_request)

    def _mangle_digits(self, fuzzable_request):
        """
        Mangle the digits (if any) in the fr URL.

        :param fuzzable_request: The original FuzzableRequest
        :return: A generator which returns mangled fuzzable requests
        """
        # First i'll mangle the digits in the URL filename
        filename = fuzzable_request.get_url().get_file_name()
        domain_path = fuzzable_request.get_url().get_domain_path()

        for fname in self._do_combinations(filename):
            fr_copy = copy.deepcopy(fuzzable_request)
            fr_copy.set_url(domain_path.url_join(fname))

            if fr_copy.get_uri() not in self._already_visited:
                self._already_visited.add(fr_copy.get_uri())

                yield fr_copy

        # Now i'll mangle the query string variables
        data_container = fuzzable_request.get_querystring()

        for _, token in data_container.iter_bound_tokens():
            for modified_value in self._do_combinations(token.get_value()):

                fr_copy = copy.deepcopy(fuzzable_request)
                qs = fr_copy.get_querystring()
                qs_token = qs.set_token(token.get_path())
                qs_token.set_value(modified_value)

                if fr_copy.get_uri() not in self._already_visited:
                    self._already_visited.add(fr_copy.get_uri())

                    yield fr_copy

    def _do_combinations(self, a_string):
        """
        >>> ds = digit_sum()
        >>> ds._do_combinations( 'abc123' )
        ['abc124', 'abc122']

        >>> ds._do_combinations( 'abc123def56' )
        ['abc124def56', 'abc122def56', 'abc123def57', 'abc123def55']

        """
        res = []
        split = self._find_digits(a_string)

        if len(split) <= 2 * self._max_digit_sections:
            for i in xrange(len(split)):
                if split[i].isdigit():
                    split[i] = str(int(split[i]) + 1)
                    res.append(''.join(split))
                    split[i] = str(int(split[i]) - 2)
                    res.append(''.join(split))

                    # restore the initial value for next loop
                    split[i] = str(int(split[i]) + 1)

        return res

    def _find_digits(self, a_string):
        """
        Finds digits in a string and returns a list with string sections.

        >>> ds = digit_sum()
        >>> ds._find_digits('foo45')
        ['foo', '45']

        >>> ds._find_digits('f001bar112')
        ['f', '001', 'bar', '112']

        :return: A list of strings.
        """
        # regexes are soooooooooooooo cool !
        return [x for x in DIGIT_REGEX.split(a_string) if x != '']

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Apply URL fuzzing to all URLs, including images, videos, zip, etc.'
        h = 'It\'s safe to leave this option as the default.'
        o = opt_factory('fuzzImages', self._fuzz_images, d, 'boolean', help=h)
        ol.add(o)

        d = 'Set the top number of sections to fuzz'
        h = 'It\'s safe to leave this option as the default. For example, with'\
            ' maxDigitSections = 1, this string wont be fuzzed: abc123def234 ;'\
            ' but this one will abc23ldd.'
        o = opt_factory('maxDigitSections',
                        self._max_digit_sections, d, 'integer', help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._fuzz_images = options_list['fuzzImages'].get_value()
        self._max_digit_sections = options_list['maxDigitSections'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to find new URL's by changing the numbers that are
        present on it.

        Two configurable parameters exist:
            - fuzzImages
            - maxDigitSections

        An example will clarify what this plugin does, let's suppose that the
        input for this plugin is:
            - http://host.tld/index1.asp

        This plugin will request:
            - http://host.tld/index0.asp
            - http://host.tld/index2.asp

        If the response for the newly generated URL's is not an 404 error, then
        the new URL is a valid one that can contain more information and
        injection points.
        """
