"""
mx_injection.py

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

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.esmre.multi_in import multi_in
from w3af.core.data.kb.vuln import Vuln


class mx_injection(AuditPlugin):
    """
    Find MX injection vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    MX_ERRORS = (
        'Unexpected extra arguments to Select',
        'Bad or malformed request',
        'Could not access the following folders',
        # Removing! Too many false positives...
        # 'A000',
        # 'A001',
        'Invalid mailbox name',
        'To check for outside changes to the folder list go to the folders page',
        'go to the folders page',
        'Query: SELECT',
        'Query: FETCH',
        'IMAP command'
    )
    _multi_in = multi_in(MX_ERRORS)

    def __init__(self):
        """
        Plugin added just for completeness... I dont really expect to find one
        of this bugs in my life... but well.... if someone , somewhere in the
        planet ever finds a bug of using this plugin... THEN my job has been
        done :P
        """
        AuditPlugin.__init__(self)

    def audit(self, freq, orig_response):
        """
        Tests an URL for mx injection vulnerabilities.

        :param freq: A FuzzableRequest
        """
        mx_injection_strings = self._get_MX_injection_strings()
        mutants = create_mutants(freq, mx_injection_strings,
                                 orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        # I will only report the vulnerability once.
        if self._has_no_bug(mutant):

            mx_error_list = self._multi_in.query(response.body)
            for mx_error in mx_error_list:
                if mx_error not in mutant.get_original_response_body():
                    
                    desc = 'MX injection was found at: %s' % mutant.found_at()
                    
                    v = Vuln.from_mutant('MX injection vulnerability', desc,
                                         severity.MEDIUM, response.id,
                                         self.get_name(), mutant)
                    
                    v.add_to_highlight(mx_error)
                    self.kb_append_uniq(self, 'mx_injection', v)
                    break

    def _get_MX_injection_strings(self):
        """
        Gets a list of strings to test against the web app.

        :return: A list with all mx_injection strings to test. Example: [ '\"','f00000']
        """
        mx_injection_strings = ['"', 'iDontExist', '']
        return mx_injection_strings

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will find MX injections. This kind of web application errors
        are mostly seen in webmail software. The tests are simple, for every
        injectable parameter a string with special meaning in the mail server is
        sent, and if in the response I find a mail server error, a vulnerability
        was found.
        """
