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

    def audit(self, freq, orig_response):
        """
        Tests an URL for shell shock vulnerabilities.

        :param freq: A FuzzableRequest
        """
        url = freq.get_url()

        # Here the script is vulnerable, not a specific parameter, so we
        # run unique tests per URL
        if url not in self.already_tested_urls:
            self.already_tested_urls.add(url)

            # We are implementing time delays for detecting shell shock vulns
            # pull-requests are welcome for detecting using other methods
            self._with_time_delay(freq)

    def _with_time_delay(self, freq):
        """
        Tests an URLs for shell shock vulnerabilities using time delays.

        :param freq: A FuzzableRequest
        """
        headers = freq.get_headers()
        headers[TEST_HEADER] = ''
        freq.set_headers(headers)

        fuzzer_config = {'fuzzable_headers': [TEST_HEADER]}

        mutant = HeadersMutant.create_mutants(freq, [''], [TEST_HEADER],
                                              False, fuzzer_config)[0]

        for delay_obj in self.DELAY_TESTS:
            ed = ExactDelayController(mutant, delay_obj, self._uri_opener)
            success, responses = ed.delay_is_controlled()

            if success:
                mutant.set_token_value(delay_obj.get_string_for_delay(3))
                desc = 'Shell shock was found at: %s' % mutant.found_at()

                v = Vuln.from_mutant('Shell shock vulnerability', desc,
                                     severity.HIGH, [r.id for r in responses],
                                     self.get_name(), mutant)

                self.kb_append_uniq(self, 'shell_shock', v)
                break

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin detects shell shock vulnerabilities.

        See: CVE-2014-6271
        """