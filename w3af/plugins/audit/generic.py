# -*- encoding: utf-8 -*-
"""
generic.py

Copyright 2007 Andres Riancho

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
from itertools import izip, repeat

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL, FLOAT
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.fuzzer.utils import rand_number, rand_alnum
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.db.disk_list import DiskList
from w3af.core.controllers.threads.threadpool import one_to_many
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import relative_distance


class generic(AuditPlugin):
    """
    Find all kind of bugs without using a fixed error database.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        #   Internal variables
        self._potential_vulns = DiskList(table_prefix='generic')

        #   User configured variables
        self._diff_ratio = 0.30
        self._extensive = False

    def audit(self, freq, original_response, debugging_id):
        """
        Find all kind of "generic" bugs without using a fixed error database

        :param freq: A FuzzableRequest
        :param original_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # Prevent some false positives for cases where the original response
        # is already triggering an error
        if original_response.get_code() == 500:
            return

        # Get the original response and create the mutants
        mutants = create_mutants(freq, ['', ], orig_resp=original_response)

        original_response_repeat = repeat(original_response)
        args_iterator = izip(original_response_repeat, mutants)
        check_mutant = one_to_many(self._check_mutant)

        self.worker_pool.imap_unordered(check_mutant, args_iterator)

    def _check_mutant(self, original_response, mutant):
        # First I check that the current modified parameter in the mutant
        # doesn't have an already reported vulnerability. I don't want to
        # report vulnerabilities more than once.
        if self._has_potential_vuln(mutant):
            return

        # Now, we request the limit (something that doesn't exist)
        # If http://localhost/a.php?b=1
        #   * Then I should request b=12938795 (random number)
        #
        # If http://localhost/a.php?b=abc
        #   * Then I should request b=hnv98yks (random alnum)
        limit_response = self._get_limit_response(mutant)

        # Now I request something that could generate an error
        # If http://localhost/a.php?b=1
        #   * Then I should request b=<payload>
        for payload_string in self._get_payloads():

            mutant.set_token_value(payload_string)
            error_response = self._uri_opener.send_mutant(mutant)

            self._analyze_responses(original_response,
                                    limit_response,
                                    error_response,
                                    mutant)

    def _get_payloads(self):
        """
        :return: A payload list, size depends on the "extensive" user configured
                 parameter. Most payloads came from [0]!

                 [0] https://github.com/minimaxir/big-list-of-naughty-strings/
        """
        # This is the reduced payload set which is effective in triggering
        # most of the errors you'll find
        payloads = [u'1/0',
                    u'Ω≈ç√∫˜µ≤≥÷',
                    u'<>?:"{}|_+\',./;\'[]\\-=',
                    u'%*.*s',
                    u'']

        # Add more payloads if the user wants to perform a detailed scan
        if self._extensive:
            payloads += [u'undefined',
                         u'undef',
                         u'null',
                         u'NULL',
                         u'nil',
                         u'NIL',
                         u'true',
                         u'false',
                         u'True',
                         u'False',
                         u'None',
                         u'-1',
                         u'0.0/0',
                         u'NaN',
                         u'Infinity',
                         u"$ENV{'HOME'}",
                         u'00˙Ɩ$-',
                         ]

        return set(payloads)

    def _add_potential_vuln(self, mutant, id_list):
        """
        Stores the information about the potential vulnerability

        :param mutant: The mutant, containing the payload which triggered the
                       HTTP response with the error.
        :param id_list: The HTTP response ids associated with the error
        :return: None
        """
        self._potential_vulns.append((mutant.get_url(),
                                      mutant.get_token_name(),
                                      mutant,
                                      id_list))

    def _has_potential_vuln(self, mutant):
        """
        :param mutant: The mutant to verify
        :return: True if the mutant is already tagged as a potential vuln
        """
        for url, token_name, stored_mutant, id_list in self._potential_vulns:
            if mutant.get_url() != url:
                continue

            if mutant.get_token_name() != token_name:
                continue

            return True

        return False

    def _analyze_responses(self, orig_resp, limit_response, error_response,
                           mutant):
        """
        Analyze responses using various methods.
        :return: None
        """
        for analyzer in {self._analyze_code, self._analyze_body}:
            is_vuln = analyzer(orig_resp, limit_response,
                               error_response, mutant)
            if is_vuln:
                break

    def _analyze_code(self, orig_resp, limit_response, error_response, mutant):
        """
        :return: True if we found a bug using the response code
        """
        if error_response.get_code() == 500 and \
           limit_response.get_code() != 500:

            id_list = [orig_resp.id, limit_response.id, error_response.id]
            self._add_potential_vuln(mutant, id_list)

            return True

        return False

    def _analyze_body(self, orig_resp, limit_response, error_response, mutant):
        """
        :return: True if we found a bug by comparing the response bodies
        """
        original_to_error = relative_distance(orig_resp.get_body(),
                                              error_response.get_body())
        limit_to_error = relative_distance(limit_response.get_body(),
                                           error_response.get_body())
        original_to_limit = relative_distance(limit_response.get_body(),
                                              orig_resp.get_body())

        ratio = self._diff_ratio + (1 - original_to_limit)

        if original_to_error < ratio and limit_to_error < ratio:
            # Maybe the limit I requested wasn't really a non-existent one
            # (and the error page really found the limit),
            # let's request a new limit (one that hopefully doesn't exist)
            # in order to remove some false positives
            limit_response_2 = self._get_limit_response(mutant)
            limit_to_limit = relative_distance(limit_response_2.get_body(),
                                               limit_response.get_body())

            if limit_to_limit > 1 - self._diff_ratio:
                # The two limits are "equal"; It's safe to suppose that we have
                # found the limit here and that the error string really produced
                # an error
                id_list = [orig_resp.id, limit_response.id, error_response.id]
                self._add_potential_vuln(mutant, id_list)

    def _get_limit_response(self, mutant):
        """
        We request the limit (something that doesn't exist)
            - If http://localhost/a.php?b=1
                then I should request b=12938795 (random number)
            - If http://localhost/a.php?b=abc
                then I should request b=hnv98yks (random alnum)

        :return: The limit response object
        """
        mutant_copy = mutant.copy()

        is_digit = mutant.get_token_original_value().isdigit()
        value = rand_number(length=8) if is_digit else rand_alnum(length=8)
        mutant_copy.set_token_value(value)
        limit_response = self._uri_opener.send_mutant(mutant_copy)

        return limit_response

    def end(self):
        """
        This method is called when the plugin wont be used anymore.
        """
        for url, variable, mutant, id_list in self._potential_vulns:
            for info in kb.kb.get_all_findings_iter():
                if info.get_token_name() == variable and info.get_url() == url:
                    break
            else:
                desc = ('An unhandled error, which could potentially translate'
                        ' to a vulnerability, was found at: %s')
                desc %= mutant.found_at()
                
                v = Vuln.from_mutant('Unhandled error in web application', desc,
                                     severity.LOW, id_list, self.get_name(),
                                     mutant)
        
                self.kb_append_uniq(self, 'generic', v)
        
        self._potential_vulns.cleanup()
                
    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = ('Ratio to use when comparing two HTTP response bodies, if two'
             ' strings have a ratio less than diff_ratio, then they are'
             ' really different.')
        o = opt_factory('diff_ratio', self._diff_ratio, d, FLOAT)
        ol.add(o)

        d = ('When enabled this plugin will send an extended payload set which'
             ' might trigger bugs and vulnerabilities which are not found by'
             ' the default (reduced, fast) payload set.')
        o = opt_factory('extensive', self._extensive, d, BOOL)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._diff_ratio = options_list['diff_ratio'].get_value()
        self._extensive = options_list['extensive'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies unhandled Web application exceptions by sending
        specially crafted strings to each application input.
        """
