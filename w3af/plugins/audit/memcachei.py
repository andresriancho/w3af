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
from functools import partial

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.misc.diff import chunked_diff
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln


MemcacheInjection = namedtuple('MemcacheInjection',
                               ['ok', 'error_1', 'error_2'])


class memcachei(AuditPlugin):

    OK = u'key1 0 30 1\r\n1\r\nset injected 0 10 10\r\n1234567890\r\n'
    ERROR_1 = u'key1 0 f 1\r\n1\r\n'
    ERROR_2 = u'key1 0 30 0\r\n1\r\n'

    def __init__(self):
        AuditPlugin.__init__(self)
        self._eq_limit = 0.97

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for memcache injection vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        try:
            self.batch_injection_test(freq, orig_response, debugging_id)
        except HTTPRequestException:
            # No need to log, it gets logged at the xurllib level
            pass

    def batch_injection_test(self, freq, orig_response, debugging_id):
        """
        Uses the batch injection technique to find memcache injections
        """
        mutants = create_mutants(freq, [''])

        self._send_mutants_in_threads(self._analyze_echo,
                                      mutants,
                                      callback=lambda x, y: None,
                                      debugging_id=debugging_id,
                                      original_response=orig_response)

    def _analyze_echo(self, mutant, debugging_id=None, original_response=None):
        """
        :param mutant: The mutant where we should inject the payloads
        :param debugging_id: The debugging ID for this audit() session
        :param original_response: The original response for the fuzzable request
        :return: None
        """
        send_clean = partial(self._uri_opener.send_clean, debugging_id=debugging_id)
        orig_body = original_response.get_body()

        # trying to break normal execution flow with ERROR_1 payload
        mutant.set_token_value(self.ERROR_1)
        error_1_response, body_error_1_response = send_clean(mutant)

        if orig_body == error_1_response.get_body():
            #
            # Nothing to do here, the responses are equal, we don't control any
            # of it using HTTP request parameters
            #
            return

        compare_diff = False

        if self.equal_with_limit(orig_body, body_error_1_response):
            #
            # if we manage to break execution flow with the invalid memcache
            # syntax, there is a potential injection otherwise - no injection!
            #
            compare_diff = True

        # trying the correct injection request, to confirm that we've found
        # it!
        mutant.set_token_value(self.OK)
        ok_response, body_ok_response = send_clean(mutant, grep=False)

        if self.equal_with_limit(body_error_1_response,
                                 body_ok_response,
                                 compare_diff=compare_diff):
            #
            # The "OK" and "ERROR_1" responses are equal, this means that
            # we're not in a memcached injection
            #
            return

        # ERROR_2 request to just make sure that we're in a memcached case
        mutant.set_token_value(self.ERROR_2)
        error_2_response, body_error_2_response = send_clean(mutant, grep=False)

        if self.equal_with_limit(orig_body,
                                 body_error_2_response,
                                 compare_diff=compare_diff):
            #
            # now requests should be different again, otherwise injection
            # is not confirmed
            #
            return

        # The two errors should look very similar for a memcache inj to exist
        if not self.equal_with_limit(body_error_1_response,
                                     body_error_2_response,
                                     compare_diff=compare_diff):
            return

        response_ids = [error_1_response.id,
                        ok_response.id,
                        error_2_response.id]

        desc = ('Memcache injection was found at: "%s", using'
                ' HTTP method %s. The injectable parameter is: "%s"')
        desc %= (mutant.get_url(),
                 mutant.get_method(),
                 mutant.get_token_name())

        v = Vuln.from_mutant('Memcache injection vulnerability', desc,
                             severity.HIGH, response_ids, 'memcachei',
                             mutant)

        self.kb_append_uniq(self, 'memcachei', v)

    def equal_with_limit(self, body1, body2, compare_diff=False):
        """
        Determines if two pages are equal using a ratio, if compare_diff is set
        then we just compare the parts of the response bodies which are different.
        """
        if compare_diff:
            body1, body2 = chunked_diff(body1, body2)

        cmp_res = fuzzy_equal(body1, body2, self._eq_limit)
        return cmp_res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies memcache injections using error based techniques,
        it can identify these injection types:

            * Batch injection (command injection) - 0x0a/0x0d bytes
        """