"""
blind_sqli_response_diff.py

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
import urllib
import cgi

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.fuzzer.utils import rand_number
from w3af.core.controllers.misc.levenshtein import relative_distance_boolean
from w3af.core.controllers.misc.diff import diff


class blind_sqli_response_diff(object):
    """
    This class tests for blind SQL injection bugs using response diffs,
    the logic is here and not as an audit plugin because it is also used in
    attack plugins when trying to verify the vulnerability.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, uri_opener):
        # User configured variables
        self._eq_limit = 0.8
        self._uri_opener = uri_opener

    def set_eq_limit(self, eq_limit):
        """
        Most of the equal algorithms use a rate to tell if two responses
        are equal or not. 1 is 100% equal, 0 is totally different.

        :param eq_limit: The equal limit to use.
        """
        self._eq_limit = eq_limit

    def is_injectable(self, mutant):
        """
        Check if "parameter" of the fuzzable request object is injectable or not.

        @mutant: The mutant object that I have to inject to
        @param: A string with the parameter name to test

        :return: A vulnerability object or None if nothing is found
        """
        statements = self._get_statements(mutant)
        for statement_type in statements:
            vuln = self._find_bsql(mutant, statements[statement_type],
                                   statement_type)
            if vuln:
                return vuln

        return None

    def _get_statements(self, mutant, exclude_numbers=[]):
        """
        Returns a list of statement tuples.
        """
        res = {}
        rnd_num = int(rand_number(2, exclude_numbers))
        rnd_num_plus_one = rnd_num + 1

        # Numeric/Datetime
        true_stm = '%i OR %i=%i ' % (rnd_num, rnd_num, rnd_num)
        false_stm = '%i AND %i=%i ' % (rnd_num, rnd_num, rnd_num_plus_one)
        res['numeric'] = (true_stm, false_stm)

        # Single quotes
        true_stm = "%i' OR '%i'='%i" % (rnd_num, rnd_num, rnd_num)
        false_stm = "%i' AND '%i'='%i" % (rnd_num, rnd_num, rnd_num_plus_one)
        res['stringsingle'] = (true_stm, false_stm)

        # Double quotes
        true_stm = '%i" OR "%i"="%i' % (rnd_num, rnd_num, rnd_num)
        false_stm = '%i" AND "%i"="%i' % (rnd_num, rnd_num, rnd_num_plus_one)
        res['stringdouble'] = (true_stm, false_stm)

        return res

    def _find_bsql(self, mutant, statement_tuple, statement_type):
        """
        Is the main algorithm for finding blind SQL injections.

        :return: A vulnerability object or None if nothing is found
        """
        true_statement = statement_tuple[0]
        false_statement = statement_tuple[1]

        mutant.set_mod_value(true_statement)
        _, body_true_response = self.send_clean(mutant)

        mutant.set_mod_value(false_statement)
        _, body_false_response = self.send_clean(mutant)

        if body_true_response == body_false_response:
            #
            #    There is NO CHANGE between the true and false responses.
            #    NO WAY I'm going to detect a blind SQL injection using
            #    response diffs in this case.
            #
            return None

        compare_diff = False

        om.out.debug('Comparing body_true_response and body_false_response.')
        if self.equal_with_limit(body_true_response, body_false_response,
                                 compare_diff):
            #
            #    They might be equal because of various reasons, in the best
            #    case scenario there IS a blind SQL injection but the % of the
            #    HTTP response body controlled by it is so small that the equal
            #    ratio is not catching it.
            #
            compare_diff = True

        syntax_error = "d'z'0"
        mutant.set_mod_value(syntax_error)
        syntax_error_response, body_syntax_error_response = self.send_clean(
            mutant)

        self.debug(
            'Comparing body_true_response and body_syntax_error_response.')
        if self.equal_with_limit(body_true_response,
                                 body_syntax_error_response,
                                 compare_diff):
            return None
        
        # Verify the injection!
        statements = self._get_statements(mutant)
        second_true_stm = statements[statement_type][0]
        second_false_stm = statements[statement_type][1]

        mutant.set_mod_value(second_true_stm)
        second_true_response, body_second_true_response = self.send_clean(
            mutant)

        mutant.set_mod_value(second_false_stm)
        second_false_response, body_second_false_response = self.send_clean(mutant)

        self.debug(
            'Comparing body_second_true_response and body_true_response.')
        if not self.equal_with_limit(body_second_true_response,
                                     body_true_response,
                                     compare_diff):
            return None
        
        self.debug('Comparing body_second_false_response and body_false_response.')
        if self.equal_with_limit(body_second_false_response,
                                 body_false_response,
                                 compare_diff):
            
            response_ids = [second_false_response.id,
                            second_true_response.id]
            
            desc = 'Blind SQL injection was found at: "%s", using'\
                   ' HTTP method %s. The injectable parameter is: "%s"'
            desc = desc % (mutant.get_url(),
                           mutant.get_method(),
                           mutant.get_var())
            
            v = Vuln.from_mutant('Blind SQL injection vulnerability', desc,
                                 severity.HIGH, response_ids, 'blind_sqli',
                                 mutant)
            
            om.out.debug(v.get_desc())

            v['type'] = statement_type
            v['true_html'] = second_true_response.get_body()
            v['false_html'] = second_false_response.get_body()
            v['error_html'] = syntax_error_response.get_body()
            return v

        return None

    def debug(self, msg):
        om.out.debug('[blind_sqli_debug] ' + msg)

    def equal_with_limit(self, body1, body2, compare_diff=False):
        """
        Determines if two pages are equal using a ratio.
        """
        if compare_diff:
            body1, body2 = diff(body1, body2)

        cmp_res = relative_distance_boolean(body1, body2, self._eq_limit)
        self.debug('Result: %s' % cmp_res)

        return cmp_res

    def send_clean(self, mutant):
        """
        Sends a mutant to the network (without using the cache) and then returns
        the HTTP response object and a sanitized response body (which doesn't
        contain any traces of the injected payload).

        The sanitized version is useful for having clean comparisons between two
        responses that were generated with different mutants.

        :param mutant: The mutant to send to the network.
        :return: (
                    HTTP response,
                    Sanitized HTTP response body,
                 )
        """
        http_response = self._uri_opener.send_mutant(mutant, cache=False)
        clean_body = get_clean_body(mutant, http_response)

        return http_response, clean_body


def get_clean_body(mutant, response):
    """
    @see: Very similar to fingerprint_404.py get_clean_body() bug not quite
          the same maybe in the future I can merge both?

    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/?id=1 OR 23=23
            - response.get_body() == '...<x>1 OR 23=23</x>...'

        - output:
            - self._clean_body( response ) == '...<x></x>...'

    All injected values are removed encoded and "as is".

    :param mutant: The mutant where I can get the value from.
    :param response: The HTTPResponse object to clean
    :return: A string that represents the "cleaned" response body.
    """

    body = response.body

    if response.is_text_or_html():
        mod_value = mutant.get_mod_value()

        body = body.replace(mod_value, '')
        body = body.replace(urllib.unquote_plus(mod_value), '')
        body = body.replace(cgi.escape(mod_value), '')
        body = body.replace(cgi.escape(urllib.unquote_plus(mod_value)), '')

    return body
