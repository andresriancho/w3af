"""
payload_test_helper.py

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
import w3af.core.data.kb.config as cf

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class PayloadTestHelper(PluginTest):

    target_url = get_moth_http('/audit/local_file_read/'
                               'local_file_read.py?file=section.txt')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('lfi'),),
            }
        }
    }

    # FIXME: For each (very small) payload test, a new scan is run. I need to
    #        experiment with setUpClass or setUpModule to fix this awful
    #        test performance issue.
    def _scan_wrapper(self):
        """
        :return: Run the scan and return the vulnerability itself and the
                 vuln_id.
        """
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('lfi', 'lfi')
        self.assertEquals(1, len(vulns))

        vuln = vulns[0]
        vuln_to_exploit_id = vuln.get_id()

        return vuln, vuln_to_exploit_id

    def _get_shell(self):
        vuln, vuln_to_exploit_id = self._scan_wrapper()

        plugin = self.w3afcore.plugins.get_plugin_inst('attack',
                                                       'local_file_reader')

        self.assertTrue(plugin.can_exploit(vuln_to_exploit_id))

        exploit_result = plugin.exploit(vuln_to_exploit_id)

        self.assertGreaterEqual(len(exploit_result), 1)

        shell = exploit_result[0]
        return shell

    def setUp(self):
        super(PayloadTestHelper, self).setUp()
        cf.cf.save('target_os', 'unix')
        self.shell = self._get_shell()

    def tearDown(self):
        super(PayloadTestHelper, self).tearDown()
        cf.cf.save('target_os', 'unknown')
