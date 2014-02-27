"""
test_rfi.py

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

from w3af.plugins.tests.helper import PluginConfig, ExecExploitTest
from w3af.core.data.kb.vuln_templates.rfi_template import RFITemplate


@attr('smoke')
class TestRFI(ExecExploitTest):

    target_url = 'http://moth/w3af/audit/rfi/vulnerable.php'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('rfi'),),
            }
        }
    }

    @attr('ci_fails')
    def test_found_exploit_rfi(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'] + '?file=section.php', cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(1, len(vulns))

        vuln = vulns[0]
        self.assertEquals(vuln.get_name(), 'Remote code execution')
        self.assertEquals(vuln.get_url().url_string, self.target_url)

        vuln_to_exploit_id = vuln.get_id()
        self._exploit_vuln(vuln_to_exploit_id, 'rfi')
    
    @attr('ci_fails')
    def test_from_template(self):
        rfit = RFITemplate()
        
        options = rfit.get_options()
        options['url'].set_value('http://moth/w3af/audit/rfi/vulnerable.php')
        options['data'].set_value('file=section.php')
        options['vulnerable_parameter'].set_value('file')
        rfit.set_options(options)

        rfit.store_in_kb()
        vuln = self.kb.get(*rfit.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()
        
        self._exploit_vuln(vuln_to_exploit_id, 'rfi')