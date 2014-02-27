"""
test_xpath.py

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


class TestXPATH(PluginTest):

    target_url = 'http://moth/w3af/audit/xpath/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('xpath'),),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        }
    }

    @attr('ci_fails')
    def test_found_xpath(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        expected_vuln_number = 4
        vulns = self.kb.get('xpath', 'xpath')
        self.assertEquals(expected_vuln_number, len(vulns), vulns)
        
        vtitle = "XPATH injection vulnerability"
        all_titles = all([vtitle == vuln.get_name() for vuln in vulns])
        self.assertTrue(all_titles, vulns)

        # Verify the specifics about the vulnerabilities
        expected = [
            ('xpath-tag.php', 'input'),
            ('xpath-attr-single.php', 'input'),
            ('xpath-attr-double.php', 'input'),
            ('xpath-or.php', 'input')
        ]

        verified_vulns = 0
        for vuln in vulns:
            if (vuln.get_url().get_file_name(), vuln.get_mutant().get_var()) in expected:
                verified_vulns += 1

        self.assertEquals(expected_vuln_number, verified_vulns)