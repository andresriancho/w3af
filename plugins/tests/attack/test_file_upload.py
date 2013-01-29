'''
test_file_upload.py

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
'''
from plugins.tests.helper import PluginTest, PluginConfig


class TestFileUploadShell(PluginTest):

    file_upload_url = 'http://moth/w3af/audit/file_upload/'

    _run_configs = {
        'cfg': {
            'target': file_upload_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'file_upload', ('extensions',
                                        'gif,html,bmp,jpg,png,txt',
                                        PluginConfig.LIST)
                    ),)
            }, }
    }

    def test_found_exploit_file_upload(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('file_upload', 'file_upload')
        self.assertEquals(1, len(vulns))
        
        vuln = vulns[0]
        
        self.assertEquals("Insecure file upload", vuln.get_name())

        vuln_to_exploit_id = vuln.get_id()

        plugin = self.w3afcore.plugins.get_plugin_inst('attack', 'file_upload')

        self.assertTrue(plugin.can_exploit(vuln_to_exploit_id))

        exploit_result = plugin.exploit(vuln_to_exploit_id)

        self.assertGreaterEqual(len(exploit_result), 1)

        #
        # Now I start testing the shell itself!
        #
        shell = exploit_result[0]
        
        etc_passwd = shell.generic_user_input('read', ['/etc/passwd',])
        self.assertTrue('root' in etc_passwd)
        self.assertTrue('/bin/bash' in etc_passwd)
        
        etc_passwd = shell.generic_user_input('e', ['cat', '/etc/passwd',])
        self.assertTrue('root' in etc_passwd)
        self.assertTrue('/bin/bash' in etc_passwd)
        
        lsp = shell.generic_user_input('lsp', [])
        self.assertTrue('apache_config_directory' in lsp)

        payload = shell.generic_user_input('payload', ['apache_config_directory'])
        self.assertTrue(payload is None)
