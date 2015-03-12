"""
memcachei.py

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
from collections import namedtuple

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_not_equal
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln


MemcacheInjection = namedtuple('MemcacheInjection', ['ok', 'error_1', 'error_2'])


class memcachei(AuditPlugin):

    def __init__(self):
        AuditPlugin.__init__(self)
        self.mci = MemcacheInjection(u'key1 0 30 1\r\n1\r\n'
                                     u'set injected 0 10 10\r\n1234567890\r\n',
                                     u'key1 0 f 1\r\n1\r\n',
                                     u'key1 0 30 0\r\n1\r\n')
        self._eq_limit = 0.97

    def audit(self, freq, orig_response):
        """
        Tests an URL for memcache injection vulnerabilities.
        """
        try:
            self.batch_injection_test(freq, orig_response)
        except HTTPRequestException:
            # No need to log, it gets logged at the xurllib level
            pass

    def batch_injection_test(self, freq, orig_response):
        """
        Uses the batch injection technique to find memcache injections
        """
        # shortcut
        send_clean = self._uri_opener.send_clean

        # first checking error response
        fake_mutants = create_mutants(freq, ['', ])

        for mutant in fake_mutants:

            orig_body = orig_response.get_body()

            # trying to break normal execution flow with error1 payload
            mutant.set_token_value(self.mci.error_1)
            error_1_response, body_error_1_response = send_clean(mutant)

            if fuzzy_equal(orig_body, body_error_1_response, self._eq_limit):
                #
                # if we manage to break execution flow, there is a potential
                # injection otherwise - no injection!
                #
                continue

            # trying the correct injection request, to confirm that we've found
            # it!

            mutant.set_token_value(self.mci.ok)
            ok_response, body_ok_response = send_clean(mutant)

            if fuzzy_not_equal(orig_body, body_ok_response, self._eq_limit):
                #
                #  now requests should be equal, otherwise injection failed!
                #
                continue

            # error2 request to just make sure that wasn't random bytes

            mutant.set_token_value(self.mci.error_2)
            error_2_response, body_error_2_response = send_clean(mutant)

            if fuzzy_equal(orig_body, body_error_2_response, self._eq_limit):
                #
                # now requests should be different again, otherwise injection
                # is not confirmed
                #
                continue

            response_ids = [error_1_response.id,
                            ok_response.id,
                            error_2_response.id]

            desc = 'Memcache injection was found at: "%s", using'\
                   ' HTTP method %s. The injectable parameter is: "%s"'
            desc = desc % (mutant.get_url(),
                           mutant.get_method(),
                           mutant.get_token_name())

            v = Vuln.from_mutant('Memcache injection vulnerability', desc,
                                 severity.HIGH, response_ids, 'memcachei',
                                 mutant)

            v['ok_html'] = ok_response.get_body()
            v['error_1_html'] = error_1_response.get_body()
            v['error_2_html'] = error_2_response.get_body()

            self.kb_append_uniq(self, 'memcachei', v)

        return

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies memcache injections using error based techniques,
        it can identify these injection types:

            * Batch injection (command injection) - 0x0a/0x0d bytes
        """