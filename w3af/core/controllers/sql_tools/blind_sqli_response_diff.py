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
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.fuzzer.utils import rand_number
from w3af.core.controllers.misc.fuzzy_string_cmp import relative_distance_boolean
from w3af.core.controllers.misc.diff import diff
from w3af.core.controllers.exceptions import HTTPRequestException


class BlindSqliResponseDiff(object):
    """
    This class tests for blind SQL injection bugs using response diffs,
    the logic is here and not as an audit plugin because it is also used in
    attack plugins when trying to verify the vulnerability.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    SPECIAL_CHARS = '"\'=()'
    SYNTAX_ERROR = u"a'b\"c'd\""
    CONFIRMATION_ROUNDS = 3

    NUMERIC = 'numeric'
    STRING_SINGLE = 'string_single'
    STRING_DOUBLE = 'string_double'
    STATEMENT_TYPES = [NUMERIC, STRING_SINGLE, STRING_DOUBLE]

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
        Check if "parameter" of the fuzzable request object is injectable or not

        @mutant: The mutant object that I have to inject to
        @param: A string with the parameter name to test

        :return: A vulnerability object or None if nothing is found
        """
        for statement_type in self.STATEMENT_TYPES:

            #
            # These confirmation rounds are just to reduce false positives
            # Note that this has a really low impact on the number of HTTP
            # requests sent during a scan because it is only run if there
            # seems to be a blind SQL injection
            #
            confirmations = 0
            for _ in xrange(self.CONFIRMATION_ROUNDS):

                # Get fresh statements with new random numbers for each
                # confirmation round.
                statements = self._get_statements(mutant)

                try:
                    vuln = self._find_bsql(mutant,
                                           statements[statement_type],
                                           statement_type)
                except HTTPRequestException:
                    continue

                # One of the confirmation rounds yields "no vuln found"
                if vuln is None:
                    msg = 'Confirmation round %s for %s failed.' % (confirmations, statement_type)
                    self.debug(msg, mutant)
                    break

                # One confirmation round succeeded
                msg = 'Confirmation round %s for %s succeeded.' % (confirmations, statement_type)
                self.debug(msg, mutant)
                confirmations += 1

                if confirmations == self.CONFIRMATION_ROUNDS:
                    return vuln

        return None

    def _get_statements(self, mutant, exclude_numbers=[]):
        """
        Returns a list of statement tuples.
        """
        res = {}
        rnd_num = int(rand_number(2, exclude_numbers))
        rnd_num_plus_one = rnd_num + 1

        num_dict = {'num': rnd_num}

        # Numeric/Datetime
        true_stm = '%(num)s OR %(num)s=%(num)s OR %(num)s=%(num)s ' % num_dict
        false_stm = '%i AND %i=%i ' % (rnd_num, rnd_num, rnd_num_plus_one)
        res[self.NUMERIC] = (true_stm, false_stm)

        # Single quotes
        true_stm = "%(num)s' OR '%(num)s'='%(num)s' OR '%(num)s'='%(num)s" % num_dict
        false_stm = "%i' AND '%i'='%i" % (rnd_num, rnd_num, rnd_num_plus_one)
        res[self.STRING_SINGLE] = (true_stm, false_stm)

        # Double quotes
        true_stm = '%(num)s" OR "%(num)s"="%(num)s" OR "%(num)s"="%(num)s' % num_dict
        false_stm = '%i" AND "%i"="%i' % (rnd_num, rnd_num, rnd_num_plus_one)
        res[self.STRING_DOUBLE] = (true_stm, false_stm)

        return res

    def _remove_all_special_chars(self, sql_statement):
        """
        :param sql_statement: A SQL injection such as 47" OR "47"="47" OR "47"="47
        :return: 47 OR 47 47 OR 47 47

        This is useful to test if the parameter we're testing is actually
        a search engine which is returning search results, and not a sql engine
        which is being injected.
        """
        for special_char in self.SPECIAL_CHARS:
            sql_statement = sql_statement.replace(special_char, ' ')

        # escape double white spaces, not sure if this has any logical value
        # in the search engine, but just in case...
        double_spaces = '  '
        while double_spaces in sql_statement:
            sql_statement = sql_statement.replace(double_spaces, ' ')

        return sql_statement

    def _find_bsql(self, mutant, statement_tuple, statement_type):
        """
        Is the main algorithm for finding blind SQL injections.

        :return: A vulnerability object or None if nothing is found
        """
        # shortcuts
        true_statement = statement_tuple[0]
        false_statement = statement_tuple[1]
        send_clean = self._uri_opener.send_clean

        mutant.set_token_value(true_statement)
        _, body_true_response = send_clean(mutant)

        mutant.set_token_value(false_statement)
        _, body_false_response = send_clean(mutant)

        if body_true_response == body_false_response:
            msg = ('There is NO CHANGE between the true and false responses.'
                   ' NO WAY w3af is going to detect a blind SQL injection'
                   ' using response diffs in this case.')
            self.debug(msg, mutant)
            return None

        compare_diff = False

        self.debug('[%s] Comparing body_true_response and'
                   ' body_false_response.' % statement_type, mutant)
        if self.equal_with_limit(body_true_response,
                                 body_false_response,
                                 compare_diff):
            #
            # They might be equal because of various reasons, in the best
            # case scenario there IS a blind SQL injection but the % of the
            # HTTP response body controlled by it is so small that the equal
            # ratio is not catching it.
            #
            self.debug('Setting compare_diff to True', mutant)
            compare_diff = True

        mutant.set_token_value(self.SYNTAX_ERROR)
        syntax_error_response, body_syntax_error_response = send_clean(mutant)

        self.debug('[%s] Comparing body_true_response and'
                   ' body_syntax_error_response.' % statement_type, mutant)
        if self.equal_with_limit(body_true_response,
                                 body_syntax_error_response,
                                 compare_diff):
            return None

        # Check if its a search engine before we dig any deeper...
        search_disambiguator = self._remove_all_special_chars(true_statement)
        mutant.set_token_value(search_disambiguator)
        _, body_search_response = send_clean(mutant)

        # If they are equal then we have a search engine
        self.debug('[%s] Comparing body_true_response and'
                   ' body_search_response.' % statement_type, mutant)
        if self.equal_with_limit(body_true_response,
                                 body_search_response,
                                 compare_diff):
            return None

        # Verify the injection!
        statements = self._get_statements(mutant)
        second_true_stm = statements[statement_type][0]
        second_false_stm = statements[statement_type][1]

        mutant.set_token_value(second_true_stm)
        second_true_response, body_second_true_response = send_clean(mutant)

        mutant.set_token_value(second_false_stm)
        second_false_response, body_second_false_response = send_clean(mutant)

        self.debug('[%s] Comparing body_second_true_response and'
                   ' body_true_response.' % statement_type, mutant)
        if not self.equal_with_limit(body_second_true_response,
                                     body_true_response,
                                     compare_diff):
            return None
        
        self.debug('[%s] Comparing body_second_false_response and'
                   ' body_false_response.' % statement_type, mutant)
        if self.equal_with_limit(body_second_false_response,
                                 body_false_response,
                                 compare_diff):
            
            response_ids = [second_false_response.id,
                            second_true_response.id]
            
            desc = 'Blind SQL injection was found at: "%s", using'\
                   ' HTTP method %s. The injectable parameter is: "%s"'
            desc %= (mutant.get_url(),
                     mutant.get_method(),
                     mutant.get_token_name())
            
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

    def debug(self, msg, mutant=None):
        if mutant is None:
            log_line = '[blind_sqli_debug] %s' % msg
        else:
            args = (id(mutant), mutant.get_token_name(), msg)
            log_line = '[blind_sqli_debug] [id: %s] [param: %s] %s' % args

        om.out.debug(log_line)

    def equal_with_limit(self, body1, body2, compare_diff=False):
        """
        Determines if two pages are equal using a ratio.
        """
        if compare_diff:
            body1, body2 = diff(body1, body2)

        cmp_res = relative_distance_boolean(body1, body2, self._eq_limit)

        args = (self._eq_limit, cmp_res)
        self.debug('Strings are similar enough with limit %s? %s' % args, None)

        return cmp_res

