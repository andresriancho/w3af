"""
response_splitting.py

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
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info

HEADER_NAME = 'vulnerable073b'
HEADER_VALUE = 'ae5cw3af'


class response_splitting(AuditPlugin):
    """
    Find response splitting vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    HEADER_INJECTION_TESTS = ("w3af\r\n" + HEADER_NAME + ": " + HEADER_VALUE,
                              "w3af\r" + HEADER_NAME + ": " + HEADER_VALUE,
                              "w3af\n" + HEADER_NAME + ": " + HEADER_VALUE)

    # A list of error strings produced by the programming framework
    # when we try to modify a header, and the HTML output is already being
    # written to the cable, or something similar.
    HEADER_ERRORS = (
        'Header may not contain more than a single header, new line detected',
        'Cannot modify header information - headers already sent')

    def __init__(self):
        AuditPlugin.__init__(self)

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for response splitting vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        mutants = create_mutants(freq, self.HEADER_INJECTION_TESTS)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        if self._has_bug(mutant):
            return

        if self._header_was_injected(mutant, response):
            desc = 'Response splitting was found at: %s' % mutant.found_at()

            v = Vuln.from_mutant('Response splitting vulnerability', desc,
                                 severity.MEDIUM, response.id,
                                 self.get_name(), mutant)

            self.kb_append_uniq(self, 'response_splitting', v)

        # When trying to send a response splitting to php 5.1.2 I get :
        # Header may not contain more than a single header, new line detected
        for error in self.HEADER_ERRORS:

            if error in response:
                desc = ('The variable "%s" at URL "%s" modifies the HTTP'
                        ' response headers, but this error was sent while'
                        ' testing for response splitting: "%s".')
                args = (mutant.get_token_name(), mutant.get_url(), error)
                desc = desc % args
                i = Info.from_mutant('Parameter modifies response headers',
                                     desc, response.id, self.get_name(),
                                     mutant)

                self.kb_append_uniq(self, 'response_splitting', i)

                return

    def _header_was_injected(self, mutant, response):
        """
        This method verifies if a header was successfully injected

        :param mutant: The mutant that was sent to generate the response
        :param response: The HTTP response where I want to find the injected
                         header.
        :return: True / False
        """
        # Get the lower case headers
        headers = response.get_lower_case_headers()

        # Analyze injection
        for header, value in headers.items():
            if HEADER_NAME in header and value.lower() == HEADER_VALUE:
                return True

            elif HEADER_NAME in header and value.lower() != HEADER_VALUE:
                msg = ('The vulnerable header was added to the HTTP response,'
                       ' but the value is not what w3af expected (%s: %s).'
                       ' Please verify manually.')
                msg = msg % (HEADER_NAME, HEADER_VALUE)
                om.out.information(msg)

                i = Info.from_mutant('Parameter modifies response headers',
                                     msg, response.id, self.get_name(),
                                     mutant)
                
                self.kb_append_uniq(self, 'response_splitting', i)
                return False

        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will find response splitting vulnerabilities.

        The detection is done by sending "w3af\\r\\nVulnerable: Yes" to every
        injection point, and reading the response headers searching for a header
        with name "Vulnerable" and value "Yes".
        """
