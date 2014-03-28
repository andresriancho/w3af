"""
test_sqlmap.py

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

from w3af.core.controllers.ci.sqlmap_testenv import get_sqlmap_testenv_http

from w3af.plugins.tests.helper import PluginConfig, ReadExploitTest
from w3af.core.data.kb.vuln_templates.sql_injection_template import SQLiTemplate


class TestSQLMapShell(ReadExploitTest):

    SQLI = get_sqlmap_testenv_http('/mysql/get_int.php?id=2')
    
    BSQLI = 'http://moth/w3af/audit/blind_sql_injection/forms/'

    _run_configs = {
        'sqli': {
            'target': SQLI,
            'plugins': {
                'audit': (PluginConfig('sqli'),),
            }
        },
                    
        'blind_sqli': {
            'target': BSQLI,
            'plugins': {
                'audit': (PluginConfig('blind_sqli'),),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        }
        
    }

    def test_found_exploit_sqlmap_sqli(self):
        # Run the scan
        cfg = self._run_configs['sqli']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('sqli', 'sqli')
        self.assertEquals(1, len(vulns), vulns)
        self.assertEquals(
            all(["SQL injection" == v.get_name() for v in vulns]),
            True)

        # Verify the specifics about the vulnerabilities
        EXPECTED = [
            ('get_int.php', 'id'),
        ]

        found_vulns = [(v.get_url().get_file_name(),
                        v.get_mutant().get_var()) for v in vulns]

        self.assertEquals(set(EXPECTED),
                          set(found_vulns))

        vuln_to_exploit_id = [v.get_id() for v in vulns
                              if v.get_url().get_file_name() == EXPECTED[0][0]][0]
        
        self._exploit_vuln(vuln_to_exploit_id, 'sqlmap')

    @attr('ci_fails')
    def test_found_exploit_sqlmap_blind_sqli(self):
        # Run the scan
        cfg = self._run_configs['blind_sqli']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        
        self.assertEquals(1, len(vulns))
        vuln = vulns[0]
        
        self.assertEquals("Blind SQL injection vulnerability", vuln.get_name())
        self.assertEquals('user', vuln.get_mutant().get_var())
        self.assertEquals('data_receptor.php', vuln.get_url().get_file_name())
        
        vuln_to_exploit_id = vuln.get_id()
        self._exploit_vuln(vuln_to_exploit_id, 'sqlmap')

    @attr('ci_fails')
    def test_from_template(self):
        sqlit = SQLiTemplate()
        
        options = sqlit.get_options()
        path = '/audit/sql_injection/where_string_single_qs.py'
        options['url'].set_value(get_moth_http(path))
        options['data'].set_value('uname=andres')
        options['vulnerable_parameter'].set_value('name')
        sqlit.set_options(options)

        sqlit.store_in_kb()
        vuln = self.kb.get(*sqlit.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()
        
        self._exploit_vuln(vuln_to_exploit_id, 'sqlmap')