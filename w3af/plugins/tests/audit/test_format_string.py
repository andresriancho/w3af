"""
test_format_string.py

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


class TestFormatString(PluginTest):

    target_url = 'http://moth/w3af/audit/format_string/format_string.php'

    _run_configs = {
        'cfg': {
            'target': target_url + '?id=1',
            'plugins': {
                'audit': (PluginConfig('format_string'),),
            }
        }
    }

    @attr('ci_fails')
    def test_found_format(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('format_string', 'format_string')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Format string vulnerability', vuln.get_name())
        self.assertEquals(self.target_url, str(vuln.get_url()))
        self.assertEquals('id', vuln.get_token_name())