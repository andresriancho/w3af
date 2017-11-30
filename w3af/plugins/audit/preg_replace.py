"""
preg_replace.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.kb.vuln import Vuln


class preg_replace(AuditPlugin):
    """
    Find unsafe usage of PHPs preg_replace.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    PREG_PAYLOAD = ['a' + ')/' * 100, ]
    PREG_ERRORS = ('Compilation failed: unmatched parentheses at offset',
                   '<b>Warning</b>:  preg_replace() [<a',
                   'Warning: preg_replace(): ')

    _multi_in = MultiIn(PREG_ERRORS)

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for unsafe usage of PHP's preg_replace.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # First I check If I get the error message from php
        mutants = create_mutants(freq, self.PREG_PAYLOAD,
                                 orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        #
        #   I will only report the vulnerability once.
        #
        if self._has_bug(mutant):
            return

        for preg_error_string in self._find_preg_error(response):
            if preg_error_string in mutant.get_original_response_body():
                continue

            desc = 'Unsafe usage of preg_replace was found at: %s'
            desc %= mutant.found_at()

            v = Vuln.from_mutant('Unsafe preg_replace usage', desc,
                                 severity.HIGH, response.id,
                                 self.get_name(), mutant)

            v.add_to_highlight(preg_error_string)
            self.kb_append_uniq(self, 'preg_replace', v)
            break

    def _find_preg_error(self, response):
        """
        This method searches for preg_replace errors in html's.

        :param response: The HTTP response object
        :return: A list of errors found on the page
        """
        res = []
        for error_match in self._multi_in.query(response.body):
            msg = ('An unsafe usage of preg_replace() function was found,'
                   ' the error that was sent by the web application is (only'
                   ' a fragment is shown): "%s", and was found in the'
                   ' response with id %s.')

            om.out.information(msg % (error_match, response.id))
            res.append(error_match)
        return res

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['grep.error_500']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will find preg_replace vulnerabilities. This PHP function
        is vulnerable when the user can control the regular expression or the
        content of the string being analyzed and the regular expression has the
        'e' modifier.

        Right now this plugin will only find preg_replace vulnerabilities when
        PHP is configured to show errors, but a new version will find "blind"
        preg_replace errors.
        """
