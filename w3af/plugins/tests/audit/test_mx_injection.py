"""
test_mx_injection.py

Copyright 2012 Andres Riancho

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

from nose.plugins.attrib import attr
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestMXInjection(PluginTest):

    target_url = 'http://moth/w3af/audit/MX_injection/mxi.php?i=f00'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('mx_injection'),),
            }
        }
    }

    @attr('ci_fails')
    def test_found_mxi(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('mx_injection', 'mx_injection')
        self.assertEquals(1, len(vulns))
        self.assertEquals(all(["MX injection vulnerability" == vuln.get_name(
        ) for vuln in vulns]), True)

        # Verify the specifics about the vulnerabilities
        expected = [
            ('mxi.php', 'i'),
        ]

        verified_vulns = 0
        for vuln in vulns:
            if (vuln.get_url().get_file_name(), vuln.get_mutant().get_var()) in expected:
                verified_vulns += 1

        self.assertEquals(1, verified_vulns)