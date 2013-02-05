'''
test_xpath.py

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
from mock import MagicMock
from nose.plugins.attrib import attr

from plugins.tests.helper import PluginTest, PluginConfig


@attr('slow')
class TestXPathShell(PluginTest):

    target_url = 'http://moth/w3af/audit/xpath/xpath-attr-single.php?input=1'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('xpath'),),
            }
        }
    }

    def test_find_exploit_xpath(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('xpath', 'xpath')
        self.assertEquals(1, len(vulns), vulns)
        
        vuln = vulns[0]
        
        self.assertEquals(vuln.get_name(), "XPATH injection vulnerability")
        
        vuln_to_exploit_id = vuln.get_id()

        plugin = self.w3afcore.plugins.get_plugin_inst('attack', 'xpath')

        self.assertTrue(plugin.can_exploit(vuln_to_exploit_id))

        exploit_result = plugin.exploit(vuln_to_exploit_id)

        self.assertEqual(len(exploit_result), 1, exploit_result)

        #
        # Now I start testing the shell itself!
        #
        shell = exploit_result[0]
        
        self.assertEqual(shell._get_data_len(), 183)
        
        # Now that I know that this worked, lets modify the method in order for
        # it to return a lower number and the getxml() process to be much
        # shorter an faster to test.
        
        shell._get_data_len = MagicMock(return_value=45)
        
        xml = shell.generic_user_input('getxml', [])
        self.assertIn('moth', xml)
        
        _help = shell.help(None)
        self.assertNotIn('execute', _help)
        self.assertNotIn('lsp', _help)
        self.assertNotIn('upload', _help)
        self.assertIn('getxml', _help)
        
    def test_from_template(self):
        self.assertTrue(False)        