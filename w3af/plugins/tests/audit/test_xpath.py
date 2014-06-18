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
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.moth import get_moth_http


class TestXPATH(PluginTest):

    target_url = get_moth_http('/audit/xpath/')

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
        expected = [(u'xpath-attr-double.py', 'text'),
                    (u'xpath-attr-tag.py', 'text'),
                    (u'xpath-attr-or.py', 'text'),
                    (u'xpath-attr-single.py', 'text')]

        found = [(v.get_url().get_file_name(),
                  v.get_mutant().get_token_name()) for v in vulns]

        self.assertEquals(set(expected), set(found))