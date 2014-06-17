"""
test_local_file_reader.py

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
from w3af.plugins.tests.helper import PluginConfig, ReadExploitTest
from w3af.core.data.kb.vuln_templates.local_file_read_template import LocalFileReadTemplate
from w3af.core.controllers.ci.moth import get_moth_http


class TestFileReadShell(ReadExploitTest):

    target_url = get_moth_http('/audit/local_file_read/'\
                               'local_file_read.py?file=section.txt')
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('lfi'),),
            }
        }
    }

    def test_find_exploit_lfi(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('lfi', 'lfi')
        self.assertEquals(1, len(vulns), vulns)
        
        vuln = vulns[0]
        
        self.assertEquals(vuln.get_name(), "Local file inclusion vulnerability")
        
        vuln_to_exploit_id = vuln.get_id()
        self._exploit_vuln(vuln_to_exploit_id, 'local_file_reader')

    def test_from_template(self):
        lfit = LocalFileReadTemplate()
        
        options = lfit.get_options()
        
        target_url = get_moth_http('/audit/local_file_read/local_file_read.py')
        options['url'].set_value(target_url)
        
        options['data'].set_value('file=section.txt')
        options['vulnerable_parameter'].set_value('file')
        options['payload'].set_value('/etc/passwd')
        options['file_pattern'].set_value('root:x:0:0:')
        lfit.set_options(options)

        lfit.store_in_kb()
        vuln = self.kb.get(*lfit.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()
        
        self._exploit_vuln(vuln_to_exploit_id, 'local_file_reader')
