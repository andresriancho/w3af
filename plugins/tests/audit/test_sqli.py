'''
test_sqli.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
'''

from ..helper import PluginTest, PluginConfig

class TestSQLI(PluginTest):
    
    sqli_url = 'http://moth/w3af/audit/sql_injection/select/sql_injection_string.php'
    
    _run_configs = {
        'cfg': {
            'target': sqli_url + '?name=xxx',
            'plugins': (PluginConfig('audit.sqli'),),
            }
        }
    def test_found_sqli(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        sqlivulns = self.kb.getData('sqli', 'sqli')
        self.assertEquals(1, len(sqlivulns))
        # Now some tests around specific details of the found vuln
        sqlivuln = sqlivulns[0]
        self.assertEquals("You have an error in your SQL syntax;",
                          sqlivuln['error'])
        self.assertEquals("MySQL database", sqlivuln['db'])
        self.assertEquals(self.sqli_url, str(sqlivuln.getURL()))