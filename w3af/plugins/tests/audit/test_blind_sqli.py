"""
test_blind_sqli.py

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
from w3af.core.controllers.ci.moth import get_moth_http


class TestBlindSQLI(PluginTest):

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                'audit': (PluginConfig('blind_sqli'),),
            }
        }
    }

    def test_integer(self):
        target_url = get_moth_http('/audit/blind_sqli/where_integer_qs.py')
        qs = '?id=1'
        self._scan(target_url + qs, self._run_configs['cfg']['plugins'])

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals(
            "Blind SQL injection vulnerability", vuln.get_name())
        self.assertFalse('time delays' in vuln.get_desc())
        self.assertEquals("numeric", vuln['type'])
        self.assertEquals(target_url, str(vuln.get_url()))

    def test_single_quote(self):
        target_url = get_moth_http('/audit/blind_sqli/where_string_single_qs.py')
        qs = '?uname=pablo'
        self._scan_single_quote(target_url, qs)

    def test_single_quote_non_true_value_as_init(self):
        target_url = get_moth_http('/audit/blind_sqli/where_string_single_qs.py')
        qs = '?uname=foobar39'
        self._scan_single_quote(target_url, qs)

    def _scan_single_quote(self, target_url, qs):
        self._scan(target_url + qs, self._run_configs['cfg']['plugins'])

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals(
            "Blind SQL injection vulnerability", vuln.get_name())
        self.assertFalse('time delays' in vuln.get_desc())
        self.assertEquals("stringsingle", vuln['type'])
        self.assertEquals(target_url, str(vuln.get_url()))

    @attr('ci_fails')
    def test_single_quote_random(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/bsqli_string_rnd.php'
        qs = '?email=andres@w3af.org'
        self._scan(target_url + qs, self._run_configs['cfg']['plugins'])

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals(
            vuln.get_name(), 'Blind SQL injection vulnerability')
        self.assertEquals(target_url, str(vuln.get_url()))

    @attr('ci_fails')
    def test_delay_integer(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/completely_bsqli_integer.php'
        qs = '?id=1'
        self._scan(target_url + qs, self._run_configs['cfg']['plugins'])

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals(
            'Blind SQL injection vulnerability', vuln.get_name())
        self.assertTrue('time delays' in vuln.get_desc())
        self.assertEquals(target_url, str(vuln.get_url()))

    @attr('ci_fails')
    def test_delay_string_single(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/completely_bsqli_single.php'
        qs = '?email=andres@w3af.org'
        self._scan(target_url + qs, self._run_configs['cfg']['plugins'])

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals(
            'Blind SQL injection vulnerability', vuln.get_name())
        self.assertTrue('time delays' in vuln.get_desc())
        self.assertEquals(target_url, str(vuln.get_url()))

    @attr('ci_fails')
    def test_delay_string_double(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/completely_bsqli_double.php'
        qs = '?email=andres@w3af.org'
        self._scan(target_url + qs, self._run_configs['cfg']['plugins'])

        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals(
            'Blind SQL injection vulnerability', vuln.get_name())
        self.assertTrue('time delays' in vuln.get_desc())
        self.assertEquals(target_url, str(vuln.get_url()))

    @attr('ci_fails')
    def test_single_quote_form(self):
        target_url = 'http://moth/w3af/audit/blind_sql_injection/forms/test_forms.html'
        self._scan(target_url, self._run_configs['cfg']['plugins'])

        action_url = 'http://moth/w3af/audit/blind_sql_injection/forms/data_receptor.php'
        vulns = self.kb.get('blind_sqli', 'blind_sqli')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals(
            'Blind SQL injection vulnerability', vuln.get_name())
        self.assertEquals("stringsingle", vuln['type'])
        self.assertFalse('time delays' in vuln.get_desc())
        self.assertEquals(action_url, str(vuln.get_url()))

    @attr('ci_fails')
    def test_false_positives(self):
        target_path = 'http://moth/w3af/audit/blind_sql_injection/'
        target_fnames = ('random_5_lines.php',
                         'random_50_lines.php',
                         'random_500_lines.php',
                         'random_5_lines_static.php',
                         'random_50_lines_static.php',
                         'random_500_lines_static.php',
                         'delay_random.php')
        qs = '?id=1'

        for target_fname in target_fnames:
            target = target_path + target_fname + qs
            self._scan(target, self._run_configs['cfg']['plugins'])

            vulns = self.kb.get('blind_sqli', 'blind_sqli')
            self.assertEquals(0, len(vulns))