"""
test_os_commanding.py

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.kb.vuln_templates.os_commanding_template import OSCommandingTemplate
from w3af.plugins.tests.helper import PluginConfig, ExecExploitTest
from w3af.plugins.attack.os_commanding import (FullPathExploitStrategy,
                                          CmdsInPathExploitStrategy,
                                          BasicExploitStrategy)


class TestOSCommandingShell(ExecExploitTest):

    target_url = get_moth_http('/audit/os_commanding/trivial_osc.py?cmd=ls')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('os_commanding'),),
            }
        }
    }

    def test_found_exploit_osc(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('os_commanding', 'os_commanding')
        self.assertEquals(1, len(vulns))
        
        vuln = vulns[0]
        self.assertEquals(vuln.get_name(), 'OS commanding vulnerability')
        self.assertEquals(vuln.get_url().get_file_name(), 'trivial_osc.py')
        self.assertEquals(vuln.get_mutant().get_token_name(), 'cmd')

        vuln_to_exploit_id = vuln.get_id()

        plugin = self.w3afcore.plugins.get_plugin_inst('attack',
                                                       'os_commanding')

        for strategy in (FullPathExploitStrategy, CmdsInPathExploitStrategy,
                         BasicExploitStrategy):
    
            # Test one strategy in each loop
            plugin.EXPLOIT_STRATEGIES = [strategy,]
    
            self.assertTrue(plugin.can_exploit(vuln_to_exploit_id))
    
            exploit_result = plugin.exploit(vuln_to_exploit_id)
    
            msg = 'Exploitation failed with strategy %s.' % strategy
            self.assertGreaterEqual(len(exploit_result), 1, msg)
    
            #
            # Now I start testing the shell itself!
            #
            shell = exploit_result[0]
            etc_passwd = shell.generic_user_input('exec', ['cat', '/etc/passwd'])
    
            self.assertTrue('root' in etc_passwd)
    
            lsp = shell.generic_user_input('lsp', [])
            self.assertTrue('apache_config_directory' in lsp)
    
            payload = shell.generic_user_input('payload',
                                               ['apache_config_directory'])
            self.assertTrue(payload is None)
            
            _help = shell.help(None)
            self.assertIn('execute', _help)
            self.assertIn('upload', _help)
    
    def test_from_template(self):
        osct = OSCommandingTemplate()
        
        options = osct.get_options()
        
        target_url = get_moth_http('/audit/os_commanding/trivial_osc.py')
        options['url'].set_value(target_url)
        options['data'].set_value('cmd=ls')
        options['vulnerable_parameter'].set_value('cmd')
        options['operating_system'].set_value('linux')
        options['separator'].set_value('')
        osct.set_options(options)

        osct.store_in_kb()
        vuln = self.kb.get(*osct.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()
        
        self._exploit_vuln(vuln_to_exploit_id, 'os_commanding')