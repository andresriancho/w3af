'''
test_blind_sqli.py

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
import core.data.constants.dbms as dbms


class TestBlindSQLI(PluginTest):
    
    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                 'audit': (PluginConfig('blindSqli'),),
                 }
            }
        }
    
    def test_integer(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/bsqli_integer.php'
        qs = '?id=1'
        self._scan( target_url + qs, self._run_configs['cfg']['plugins'] )
        
        vulns = self.kb.getData('blindSqli', 'blindSqli')
        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals( "Blind SQL injection vulnerability", vuln.getName() )
        self.assertEquals( "numeric", vuln['type'])
        self.assertEquals( target_url, str(vuln.getURL()))

    def test_single_quote(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/bsqli_string.php'
        qs = '?email=andres@w3af.org'
        self._scan( target_url + qs, self._run_configs['cfg']['plugins'] )
        
        vulns = self.kb.getData('blindSqli', 'blindSqli')
        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals( "Blind SQL injection vulnerability", vuln.getName() )
        self.assertEquals( "stringsingle", vuln['type'])
        self.assertEquals( target_url, str(vuln.getURL()))

    def test_single_quote_random(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/bsqli_string_rnd.php'
        qs = '?email=andres@w3af.org'
        self._scan( target_url + qs, self._run_configs['cfg']['plugins'] )
        
        vulns = self.kb.getData('blindSqli', 'blindSqli')
        self.assertEquals(1, len(vulns))
        
        # Given the random nature of this target script, in some cases it will be
        # detected by the time delay technique and in some other cases by the
        # response diffing. That's why we need this:
        titles = ('Blind SQL injection - MySQL database',
                  'Blind SQL injection vulnerability')
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertTrue( vuln.getName() in titles )
        self.assertEquals( target_url, str(vuln.getURL()))

    def test_delay_integer(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/completely_bsqli_integer.php'
        qs = '?id=1'
        self._scan( target_url + qs, self._run_configs['cfg']['plugins'] )
        
        vulns = self.kb.getData('blindSqli', 'blindSqli')
        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals( "Blind SQL injection - " + dbms.MYSQL, vuln.getName() )
        self.assertEquals( target_url, str(vuln.getURL()))

    def test_delay_string(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/completely_bsqli_string.php'
        qs = '?email=andres@w3af.org'
        self._scan( target_url + qs, self._run_configs['cfg']['plugins'] )
        
        vulns = self.kb.getData('blindSqli', 'blindSqli')
        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals( "Blind SQL injection - " + dbms.MYSQL, vuln.getName() )
        self.assertEquals( target_url, str(vuln.getURL()))

    def test_single_quote_form(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/test_forms.html'
        self._scan( target_url, self._run_configs['cfg']['plugins'] )
        
        action_url = 'http://moth/w3af/audit/blind_sql_injection/data_receptor.php'
        vulns = self.kb.getData('blindSqli', 'blindSqli')
        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals( "Blind SQL injection vulnerability", vuln.getName() )
        self.assertEquals( "stringsingle", vuln['type'])
        self.assertEquals( action_url, str(vuln.getURL()))
    
    def test_false_positives(self):
        target_path = 'http://moth/w3af/audit/blind_sql_injection/'
        target_fnames = ( 'random_5_lines.php',
                          'random_50_lines.php',
                          'random_500_lines.php', 
                          'random_5_lines_static.php',
                          'random_50_lines_static.php',
                          'random_500_lines_static.php',
                          'delay_random.php')
        qs = '?id=1'
        
        for target_fname in target_fnames:
            target = target_path + target_fname + qs
            self._scan( target, self._run_configs['cfg']['plugins'] )
            
            vulns = self.kb.getData('blindSqli', 'blindSqli')
            self.assertEquals(0, len(vulns))
                