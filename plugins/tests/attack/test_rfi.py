'''
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
'''
from nose.plugins.attrib import attr

from plugins.tests.helper import PluginTest, PluginConfig


@attr('smoke')
class TestRFI(PluginTest):

    target_url = 'http://moth/w3af/audit/rfi/vulnerable.php'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('rfi'),),
            }
        }
    }

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

        plugin = self.w3afcore.plugins.get_plugin_inst('attack', 'rfi')

        self.assertTrue(plugin.can_exploit(vuln_to_exploit_id))

        exploit_result = plugin.exploit(vuln_to_exploit_id)

        self.assertGreaterEqual(len(exploit_result), 1)

        #
        # Now I start testing the shell itself!
        #
        shell = exploit_result[0]
        etc_passwd = shell.generic_user_input('exec', ['cat', '/etc/passwd'])

        self.assertTrue('root' in etc_passwd)

        lsp = shell.generic_user_input('lsp', [])
        self.assertTrue('apache_config_directory' in lsp)

        payload = shell.generic_user_input(
            'payload', ['apache_config_directory'])
        self.assertTrue(payload is None)
