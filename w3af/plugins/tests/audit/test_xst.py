"""
test_xst.py

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


class TestXST(PluginTest):

    target_url = 'http://moth/w3af/'

    _run_config = {
        'target': target_url,
        'plugins': {
            'audit': (PluginConfig('xst'),),
        }
    }

    @attr('ci_fails')
    def test_found_xst(self):

        self._scan(self._run_config['target'], self._run_config['plugins'])

        vulns = self.kb.get('xst', 'xst')
        self.assertEquals(len(vulns), 1)

        self.assertEquals(all(['Cross site tracing vulnerability' == vuln.get_name()
                               for vuln in vulns]), True)