"""
test_fingerprint_os.py

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


class TestFingerprintOS(PluginTest):

    modsecurity_url = 'http://modsecurity/w3af/index.html'
    moth_url = 'http://moth/w3af/index.html'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('fingerprint_os'),)}
        }
    }

    @attr('ci_fails')
    def test_moth(self):
        """
        Test the "default" configuration for Apache+PHP.
        """
        cfg = self._run_configs['cfg']
        self._scan(self.moth_url, cfg['plugins'])

        os_str = self.kb.raw_read('fingerprint_os', 'operating_system_str')

        self.assertEqual('unix', os_str)

    @attr('ci_fails')
    def test_modsecurity(self):
        """
        Test a different configuration:
            * Mod security enabled
            * HTTP methods restricted
            * No server header
        """
        cfg = self._run_configs['cfg']
        self._scan(self.modsecurity_url, cfg['plugins'])

        os_str = self.kb.raw_read('fingerprint_os', 'operating_system_str')

        self.assertEqual('unix', os_str)