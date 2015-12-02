"""
test_xssed_dot_com.py

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

from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestXssedDotCom(PluginTest):

    vuln_url = 'http://www.alarabiya.net'
    safe_url = 'http://www.xssed.com/'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('xssed_dot_com'),)}
        }
    }

    def test_xssed_dot_com_positive(self):
        cfg = self._run_configs['cfg']
        self._scan(self.vuln_url, cfg['plugins'])

        infos = self.kb.get('xssed_dot_com', 'xss')

        self.assertEqual(len(infos), 2, infos)

        info = infos[0]

        self.assertEqual(info.get_name(), 'Potential XSS vulnerability')
        self.assertIn('According to xssed.com', info.get_desc())

    def test_xssed_dot_com_negative(self):
        cfg = self._run_configs['cfg']
        self._scan(self.safe_url, cfg['plugins'])

        infos = self.kb.get('xssed_dot_com', 'xss')

        self.assertEqual(len(infos), 0, infos)

    def test_xssed_dot_com_too_generic_12717(self):
        """
        Test for issue #12717
        https://github.com/andresriancho/w3af/issues/12717
        """
        cfg = self._run_configs['cfg']
        self._scan('https://digi.ninja', cfg['plugins'])

        infos = self.kb.get('xssed_dot_com', 'xss')

        self.assertEqual(len(infos), 0, infos)
