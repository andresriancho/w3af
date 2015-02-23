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
from w3af.core.controllers.ci.php_moth import get_php_moth_http
from w3af.core.controllers.misc.get_unused_port import get_unused_port
from w3af.core.data.kb.vuln_templates.rfi_template import RFITemplate


@attr('smoke')
class TestRFI(ExecExploitTest):

    target_url = get_php_moth_http('/audit/rfi/rfi-rce.php')
    unused_port = get_unused_port()

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('rfi',
                                       ('use_w3af_site', False, PluginConfig.BOOL),
                                       ('listen_port', unused_port, PluginConfig.INT)),),
            }
        }
    }

    def test_found_exploit_rfi(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'] + '?file=abc.txt', cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(1, len(vulns))

        vuln = vulns[0]
        self.assertEquals(vuln.get_name(), 'Remote code execution')
        self.assertEquals(vuln.get_url().url_string, self.target_url)

        vuln_to_exploit_id = vuln.get_id()
        self._exploit_vuln(vuln_to_exploit_id, 'rfi')
    
    def test_from_template(self):
        rfit = RFITemplate()
        
        options = rfit.get_options()
        options['url'].set_value(self.target_url)
        options['data'].set_value('file=abc.txt')
        options['vulnerable_parameter'].set_value('file')
        rfit.set_options(options)

        rfit.store_in_kb()
        vuln = self.kb.get(*rfit.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()
        
        self._exploit_vuln(vuln_to_exploit_id, 'rfi')