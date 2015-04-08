"""
CommonAttackMethods.py

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
import difflib

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.exceptions import BodyCutException


class CommonAttackMethods(object):

    def __init__(self):
        self._header_length = None
        self._footer_length = None

    def set_cut(self, header_end, footer_start):
        self._header_length = header_end
        self._footer_length = footer_start

    def get_cut(self):
        return self._header_length, self._footer_length

    def _guess_cut(self, body_a, body_b, expected_result):
        """
        Guesses the header and footer based on two responses and an expected
        result that should be in body_a.

        :param body_a: The response body for the request with the expected
                       result. For example, in local file read vulnerabilities
                       this should be the result of requesting
                       file.php?f=/etc/passwd

        :param body_b: The response body for the request with an invalid
                       resource. For example, in local file read vulnerabilities
                       this should be the result of requesting
                       file.php?f=/does/not/exist

        :param expected_result: The expected result that should be found in
                                body_a. For example, in local file read
                                vulnerabilities this should look like:
                                root:x:0:0:root:/root:/bin/bash

        :return: True if the cut could be defined
        """
        if expected_result not in body_a:
            return False

        if body_a == body_b:
            return False

        sequence_matcher = difflib.SequenceMatcher(lambda x: len(x) < 3,
                                                   body_a, body_b)

        body_a_len = len(body_a)
        body_b_len = len(body_b)

        longest_match = sequence_matcher.find_longest_match(0, body_a_len,
                                                            0, body_b_len)
        longest_match_a = longest_match[0]
        longest_match_b = longest_match[1]
        longest_match_size = longest_match[2]

        # This should return a long match at the beginning or the end of the
        # string
        #
        # If the longest_match is very small in relation to the whole response,
        # then we're in a case in which there is no header or footer.
        #
        # I measure against the body_b_len because in that response (generally
        # an error) the amount of bytes consumed by the "/etc/passwd" file is
        # less and allows me to calculate a more accurate ratio.
        #

        if float(longest_match_size) == body_b_len == 0 or \
          (float(longest_match_size) / body_b_len) < 0.01:
            self._footer_length = 0
            self._header_length = 0

        else:
            #
            # The match object has the following interesting attributes:
            #     a: The index where the longest match starts at body_a
            #     b: The index where the longest match starts at body_b
            #     size: Size of the longest match
            #
            # Now that I have that info, I want to know if this represents the
            # header or the footer of the response.
            #
            # We're in the case where at least we have a header, a footer or
            # both.
            #

            if longest_match_a + longest_match_size == body_a_len:
                #    The longest match is in the footer
                self._footer_length = longest_match_size

                #    Now I need to calculate the header
                longest_match_header = sequence_matcher.find_longest_match(
                                                                0, longest_match_a,
                                                                0, longest_match_b)
                longest_match_header_size = longest_match_header[2]

                #    Do we really have a header?
                if (float(longest_match_header_size) / (body_b_len - longest_match_a)) < 0.1:
                    #    No we don't
                    self._header_length = 0
                else:
                    # We have a header!
                    self._header_length = longest_match_header_size

            else:

                #    The longest match is in the header
                self._header_length = longest_match_size

                #    Now I need to calculate the footer
                #
                #    It seems that with a reverse it works better!
                #
                body_a_reverse = body_a[::-1]
                body_b_reverse = body_b[::-1]
                sequence_matcher = difflib.SequenceMatcher(lambda x: len(x) < 3,
                                                           body_a_reverse,
                                                           body_b_reverse)

                longest_match_footer = sequence_matcher.find_longest_match(
                    0, body_a_len - self._header_length,
                    0, body_b_len - self._header_length)
                longest_match_footer_size = longest_match_footer[2]

                #    Do we really have a footer?
                if (float(longest_match_footer_size) / (body_b_len - longest_match_a)) < 0.01:
                    #    No we don't
                    self._footer_length = 0
                else:
                    # We have a header!
                    self._footer_length = longest_match_footer_size

        return True

    def _define_cut_from_etc_passwd(self, body_a, body_b):
        """
        Defines the header and footer length based on the fact that we know the
        /etc/passwd file format.
        
        :param body_a: The http response body for a request that retrieves
                       /etc/passwd , without caching.
        :param body_b: The http response body for a request that retrieves
                       /etc/passwd , without caching.
        
        :return: None, we just set self._header_length and self._footer_length
                 or raise and exception if the method was not properly called.
        """
        if body_a != body_b:
            msg = '_define_cut_from_etc_passwd can only work with static'\
                  ' responses and in this case the bodies seem to be different.'
            raise ValueError(msg)
        
        etc_passwd_re = re.compile('[\w_-]*:x:\d*?:\d*?:[\w_, -]*:[/\w_-]*:[/\w_-]*')
        mo = etc_passwd_re.search(body_a)
        
        if not mo:
            msg = '_define_cut_from_etc_passwd did not find any /etc/passwd'\
                  ' contents in the HTTP response body.'
            raise ValueError(msg)
        
        match_string = mo.group(0)
        if 'root:' not in match_string:
            msg = '_define_cut_from_etc_passwd did not find "root:" in the'\
                  ' first line of /etc/passwd. The algorithm is very strict'\
                  ' and does NOT support this case.'
            raise ValueError(msg)
            
        start = mo.start()
        self._header_length = start + match_string.index('root:')
        
        all_match_lines = etc_passwd_re.findall(body_a)
        last_line = all_match_lines[-1]
        # The -1 is for the \n at the end of the last /etc/passwd line
        self._footer_length = len(body_a) - body_a.index(last_line) - len(last_line) - 1
        
        if self._footer_length == -1:
            msg = '_define_cut_from_etc_passwd detected an /etc/passwd that it'\
                  ' can NOT handle because it does NOT end in a new line.'
            raise ValueError(msg)
        
        return True

    def _define_exact_cut(self, body, expected_result):
        """
        Defines the section where the result of an attack will be.

        For example, when performing an OS Commanding attack, the command
        response could be in the middle of some HTML text. This function defines
        the header and footer attributes that are used by _cut() in order to
        extract the information from the HTML.

        :return: True if the cut could be defined
        """
        if not expected_result in body:
            # I won't be able to define the cut
            return False

        else:

            # Define the header
            self._header_length = body.find(expected_result)

            # Define the footer
            self._footer_length = len(body) - self._header_length - len(expected_result)

            om.out.debug('Defined cut header and footer using exact match')
            om.out.debug('Defined header length to %i' % self._header_length)
            om.out.debug('Defined footer length to %i' % self._footer_length)

            return True

    def _cut(self, body):
        """
        After defining a cut, I can cut parts of an HTML and return the
        important sections.

        :param body: The HTML response that I need to cut to obtain the useful
                     information.
        """
        if self._header_length is None or self._footer_length is None:
            msg = ('You need to call _define_exact_cut() or _guess_cut() before'
                   'calling _cut().')
            raise RuntimeError(msg)

        if self._header_length + self._footer_length > len(body):
            # FIXME: I should handle this in some way.
            msg = 'Cut algorithm error: len(header+footer) > len(body).'
            raise BodyCutException(msg)

        if body == '':
            om.out.debug('Called _cut() with an empty body,'
                         ' returning an empty result.')
            return body

        #   Special case where there are no header or footers,
        if self._header_length == self._footer_length == 0:
            return body

        if self._footer_length == 0:
            return body[self._header_length:]
        else:
            return body[self._header_length:-self._footer_length]
