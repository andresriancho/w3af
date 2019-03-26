"""
blind_sqli.py

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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.sql_tools.blind_sqli_response_diff import BlindSqliResponseDiff
from w3af.core.controllers.sql_tools.blind_sqli_time_delay import BlindSQLTimeDelay

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.fuzzer.fuzzer import create_mutants


class blind_sqli(AuditPlugin):
    """
    Identify blind SQL injection vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        # User configured variables
        self._eq_limit = 0.9

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for blind SQL injection vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        #
        #    Blind SQL injection response diff
        #
        bsqli_resp_diff = BlindSqliResponseDiff(self._uri_opener)
        bsqli_resp_diff.set_eq_limit(self._eq_limit)
        bsqli_resp_diff.set_debugging_id(debugging_id)

        test_iterator = self._generate_response_diff_tests(freq, bsqli_resp_diff)

        self._send_mutants_in_threads(func=self._find_response_diff_sql,
                                      iterable=test_iterator,
                                      callback=lambda x, y: None)

        #
        #    Blind SQL injection time delays
        #
        bsqli_time_delay = BlindSQLTimeDelay(self._uri_opener)
        bsqli_time_delay.set_debugging_id(debugging_id)

        test_iterator = self._generate_delay_tests(freq, bsqli_time_delay)

        self._send_mutants_in_threads(func=self._find_time_delay_sql,
                                      iterable=test_iterator,
                                      callback=lambda x, y: None)

    def _find_response_diff_sql(self, (bsqli_resp_diff, mutant, statement_type)):
        """
        :param bsqli_resp_diff: The logic used to find blind sql injections
        :param mutant: The mutant object that I have to inject to
        :param statement_type: The type of statement (string single, string double, int)
        :return: A vulnerability or None
        """
        #
        # These tests were already made in _generate_response_diff_tests() but
        # between the mutant generation and the time it is about to be sent the
        # framework might have found more vulnerabilities
        #
        if self._has_sql_injection(mutant):
            #
            # If sqli.py was enabled and already detected a vulnerability
            # in this parameter, then it makes no sense to test it again
            # and report a duplicate to the user
            #
            return

        if self._has_bug(mutant):
            #
            # If we already identified a blind SQL injection in this
            # mutant, maybe using response diff, then do not try to
            # identify the issue again using time delays
            #
            return

        vuln = bsqli_resp_diff.is_injectable(mutant, statement_type)
        self._conditionally_save_vuln(mutant, vuln)

    def _conditionally_save_vuln(self, mutant, vuln):
        """
        Save the vulnerability to the KB iff ...

        :param mutant: The mutant that triggered the vulnerability
        :param vuln: The vulnerability instance
        :return: None. Vuln is saved to KB on success.
        """
        if vuln is None:
            return

        if self._has_sql_injection(mutant):
            msg = ('There is already a SQL injection vulnerability in the'
                   ' KB for this blind SQL injection. Will not save the'
                   ' blind SQL injection (%s) to avoid duplicates.')
            args = (vuln,)
            om.out.debug(msg % args)
            return

        if self._has_bug(mutant):
            msg = ('There is already a Blind SQL injection vulnerability'
                   ' in the KB with the same URL and parameter combination.'
                   ' Will not save blind SQL injection (%s) to avoid'
                   ' duplicates.')
            args = (vuln,)
            om.out.debug(msg % args)
            return

        added_to_kb = self.kb_append_uniq(self, 'blind_sqli', vuln)

        if not added_to_kb:
            msg = ('The kb_append_uniq() returned false. The blind SQL'
                   ' injection vulnerability was NOT saved to the KB because'
                   ' another vulnerability (uniq) was stored there before.'
                   ' The blind SQL injection vulnerability that was ignored'
                   ' is: %s.')
            args = (vuln,)
            om.out.debug(msg % args)

    def _generate_response_diff_tests(self, freq, bsqli_resp_diff):
        for mutant in create_mutants(freq, ['', ]):

            if self._has_sql_injection(mutant):
                #
                # If sqli.py was enabled and already detected a vulnerability
                # in this parameter, then it makes no sense to test it again
                # and report a duplicate to the user
                #
                continue

            if self._has_bug(mutant):
                #
                # If we already identified a blind SQL injection in this
                # mutant, maybe using response diff, then do not try to
                # identify the issue again using time delays
                #
                continue

            for statement_type in bsqli_resp_diff.get_statement_types():
                yield bsqli_resp_diff, mutant, statement_type

    def _generate_delay_tests(self, freq, bsqli_time_delay):
        for mutant in create_mutants(freq, ['', ]):

            if self._has_sql_injection(mutant):
                #
                # If sqli.py was enabled and already detected a vulnerability
                # in this parameter, then it makes no sense to test it again
                # and report a duplicate to the user
                #
                continue

            if self._has_bug(mutant):
                #
                # If we already identified a blind SQL injection in this
                # mutant, maybe using response diff, then do not try to
                # identify the issue again using time delays
                #
                continue

            for delay_obj in bsqli_time_delay.get_delays():
                yield bsqli_time_delay, mutant, delay_obj

    def _find_time_delay_sql(self, (bsqli_time_delay, mutant, delay_obj)):
        """
        :param bsqli_time_delay: The logic used to find blind sql injections
        :param mutant: The mutant object that I have to inject to
        :param delay_obj: The exact delay object
        :return: A vulnerability or None
        """
        #
        # These tests were already made in _generate_delay_tests() but
        # between the mutant generation and the time it is about to be sent the
        # framework might have found more vulnerabilities
        #
        if self._has_sql_injection(mutant):
            #
            # If sqli.py was enabled and already detected a vulnerability
            # in this parameter, then it makes no sense to test it again
            # and report a duplicate to the user
            #
            return

        if self._has_bug(mutant):
            #
            # If we already identified a blind SQL injection in this
            # mutant, maybe using response diff, then do not try to
            # identify the issue again using time delays
            #
            return

        vuln = bsqli_time_delay.is_injectable(mutant, delay_obj)
        self._conditionally_save_vuln(mutant, vuln)

    def _has_sql_injection(self, mutant):
        """
        :return: True if there IS a reported SQL injection for this
                 URL/parameter combination.
        """
        for sql_injection in kb.kb.get_iter('sqli', 'sqli'):
            if sql_injection.get_url() != mutant.get_url():
                continue

            if sql_injection.get_token_name() != mutant.get_token_name():
                continue

            return True

        return False

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        opt_list = OptionList()

        desc = 'String equal ratio (0.0 to 1.0)'
        h = ('Two pages are considered equal if they match in more'
             ' than eq_limit.')
        opt = opt_factory('eq_limit', self._eq_limit, desc, 'float', help=h)

        opt_list.add(opt)

        return opt_list

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._eq_limit = options_list['eq_limit'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds blind SQL injections using two techniques: time delays
        and true/false response comparison.

        Only one configurable parameters exists:
            - eq_limit
        """
