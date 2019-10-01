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
import time

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.fuzzer.utils import rand_number
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.controllers.misc.diff import chunked_diff


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
        self._debugging_id = None

    def set_eq_limit(self, eq_limit):
        """
        Most of the equal algorithms use a rate to tell if two responses
        are equal or not. 1 is 100% equal, 0 is totally different.

        :param eq_limit: The equal limit to use.
        """
        self._eq_limit = eq_limit

    def get_statement_types(self):
        return self.STATEMENT_TYPES

    def set_debugging_id(self, debugging_id):
        self._debugging_id = debugging_id
    
    def get_debugging_id(self):
        return self._debugging_id

    def is_injectable(self, mutant, statement_type):
        """
        Check if "parameter" of the fuzzable request object is injectable or not

        :param mutant: The mutant object that I have to inject to
        :param statement_type: The type of statement (string single, string double, int)

        :return: A vulnerability object or None if nothing is found
        """
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
                self.debug(msg, mutant=mutant)
                break

            # One confirmation round succeeded
            msg = 'Confirmation round %s for %s succeeded.' % (confirmations, statement_type)
            self.debug(msg, mutant=mutant)
            confirmations += 1

            if confirmations == self.CONFIRMATION_ROUNDS:
                return vuln

    def _get_statements(self, mutant, exclude_numbers=None):
        """
        Returns a list of statement tuples.
        """
        res = {}
        exclude_numbers = exclude_numbers or []

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
        debugging_id = self.get_debugging_id()

        mutant.set_token_value(true_statement)
        true_response, body_true_response = send_clean(mutant,
                                                       debugging_id=debugging_id,
                                                       grep=True)

        mutant.set_token_value(false_statement)
        false_response, body_false_response = send_clean(mutant,
                                                         debugging_id=debugging_id,
                                                         grep=False)

        if body_true_response == body_false_response:
            msg = ('There is NO CHANGE between the true and false responses.'
                   ' NO WAY w3af is going to detect a blind SQL injection'
                   ' using response diffs in this case.')
            self.debug(msg, mutant=mutant)
            return None

        compare_diff = False

        msg = 'Comparing body_true_response and body_false_response.'
        self.debug(msg,
                   statement_type=statement_type,
                   mutant=mutant,
                   response_1=true_response,
                   response_2=false_response)

        if self.equal_with_limit(body_true_response,
                                 body_false_response,
                                 compare_diff):
            #
            # They might be equal because of various reasons, in the best
            # case scenario there IS a blind SQL injection but the % of the
            # HTTP response body controlled by it is so small that the equal
            # ratio is not catching it.
            #
            self.debug('Setting compare_diff to True', mutant=mutant)
            compare_diff = True

        mutant.set_token_value(self.SYNTAX_ERROR)
        syntax_error_response, body_syntax_error_response = send_clean(mutant,
                                                                       debugging_id=debugging_id,
                                                                       grep=False)

        msg = 'Comparing body_true_response and body_syntax_error_response.'
        self.debug(msg,
                   statement_type=statement_type,
                   mutant=mutant,
                   response_1=true_response,
                   response_2=syntax_error_response)

        if self.equal_with_limit(body_true_response,
                                 body_syntax_error_response,
                                 compare_diff):
            return None

        # Check if its a search engine before we dig any deeper...
        search_disambiguator = self._remove_all_special_chars(true_statement)
        mutant.set_token_value(search_disambiguator)
        search_response, body_search_response = send_clean(mutant,
                                                           grep=False,
                                                           debugging_id=debugging_id)

        # If they are equal then we have a search engine
        msg = 'Comparing body_true_response and body_search_response.'
        self.debug(msg,
                   statement_type=statement_type,
                   mutant=mutant,
                   response_1=true_response,
                   response_2=search_response)

        if self.equal_with_limit(body_true_response,
                                 body_search_response,
                                 compare_diff):
            return None

        # Now a nice trick from real-life. In some search engines when
        # searching for `46" OR "46"="46" OR "46"="46` we get only a
        # couple of results, which I assume is because the search
        # engine is trying to search for more terms.
        #
        # Removing the special characters will make w3af search for
        # `46  OR  46   46  OR  46   46`, which yields many results in
        # the application's search engine, which I assume is because the
        # search engine just needs to match objects with 46 / OR.
        #
        # So, this means that the responses ARE different, but they came
        # from a search engine. The check above is NOT going to catch that
        # and will yield a false positive.
        #
        # If this is not a search engine, or is a search engine with a blind
        # sql injection, the result with `46" OR "46"="46" OR "46"="46` should
        # be have a larger HTTP response body: "all results" should be there.
        #
        # If it is a search engine, then the result for the search string
        # without special characters will be larger.
        if len(body_search_response) * 0.8 > len(body_true_response):
            msg = 'Search engine detected using response length, stop.'
            self.debug(msg,
                       statement_type=statement_type,
                       mutant=mutant,
                       response_1=true_response,
                       response_2=search_response)
            return None

        # Verify the injection!
        statements = self._get_statements(mutant)
        second_true_stm = statements[statement_type][0]
        second_false_stm = statements[statement_type][1]

        mutant.set_token_value(second_true_stm)
        second_true_response, body_second_true_response = send_clean(mutant,
                                                                     grep=False,
                                                                     debugging_id=debugging_id)

        mutant.set_token_value(second_false_stm)
        second_false_response, body_second_false_response = send_clean(mutant,
                                                                       grep=False,
                                                                       debugging_id=debugging_id)

        msg = 'Comparing body_second_true_response and body_true_response.'
        self.debug(msg,
                   statement_type=statement_type,
                   mutant=mutant,
                   response_1=true_response,
                   response_2=second_true_response)

        if not self.equal_with_limit(body_second_true_response,
                                     body_true_response,
                                     compare_diff):
            return None

        msg = 'Comparing body_second_false_response and body_false_response.'
        self.debug(msg,
                   statement_type=statement_type,
                   mutant=mutant,
                   response_1=false_response,
                   response_2=second_false_response)

        if not self.equal_with_limit(body_second_false_response,
                                     body_false_response,
                                     compare_diff):
            return None
            
        response_ids = [second_false_response.id,
                        second_true_response.id]

        desc = ('Blind SQL injection was found at: "%s", using'
                ' HTTP method %s. The injectable parameter is: "%s"')
        desc %= (smart_str_ignore(mutant.get_url()),
                 smart_str_ignore(mutant.get_method()),
                 smart_str_ignore(mutant.get_token_name()))

        v = Vuln.from_mutant('Blind SQL injection vulnerability', desc,
                             severity.HIGH, response_ids, 'blind_sqli',
                             mutant)

        om.out.debug(v.get_desc())
        self.debug(v.get_desc(),
                   statement_type=statement_type,
                   mutant=mutant,
                   response_1=false_response,
                   response_2=second_false_response)

        v['type'] = statement_type
        v['true_html'] = second_true_response.get_body()
        v['false_html'] = second_false_response.get_body()
        v['error_html'] = syntax_error_response.get_body()
        return v

    def debug(self,
              msg,
              mutant=None,
              statement_type=None,
              response_1=None,
              response_2=None):
        """
        Write a message to the log

        :param msg: The message to log
        :param mutant: Mutant for [mid: ...]
        :param statement_type: Statement type for [stm: ...]
        :param response_1: HTTP response for [r1.id: ...]
        :param response_2: HTTP response for [r2.id: ...]
        :return: None, we write to the log
        """
        tags = ['[blind_sqli]']

        did = self._debugging_id
        tags.append('[did: %s]' % did)

        if mutant is not None:
            tags.append('[mid: %s]' % id(mutant))
            tags.append('[param: %s]' % mutant.get_token_name())

        if statement_type is not None:
            tags.append('[stm: %s]' % statement_type)

        if response_1 is not None:
            tags.append('[r1.id: %s]' % response_1.id)

        if response_2 is not None:
            tags.append('[r2.id: %s]' % response_2.id)

        log_line = ' '.join(tags)
        log_line += ' %s' % msg

        om.out.debug(log_line)

    def equal_with_limit(self, body1, body2, compare_diff=False):
        """
        Determines if two pages are equal using a ratio.
        """
        start = time.time()

        if compare_diff:
            body1, body2 = chunked_diff(body1, body2)

        cmp_res = fuzzy_equal(body1, body2, self._eq_limit)

        are = 'ARE' if cmp_res else 'ARE NOT'
        args = (are, self._eq_limit)
        self.debug('Strings %s similar enough (limit: %s)' % args)

        spent = time.time() - start
        self.debug('Took %.2f seconds to run equal_with_limit' % spent)

        return cmp_res

