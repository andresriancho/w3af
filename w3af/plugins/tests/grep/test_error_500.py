"""
test_error_500.py

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

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig

@attr('ci_ready')
class TestError500(PluginTest):

    error_500_url = get_moth_http('/grep/error_500/500.py?id=1')

    _run_configs = {
        'cfg1': {
            'target': error_500_url,
            'plugins': {
                'grep': (PluginConfig('error_500'),),
                'audit': (PluginConfig('sqli'),),
            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('error_500', 'error_500')

        self.assertEquals(1, len(vulns))

        vuln = vulns[0]

        self.assertEquals(
            vuln.get_name(), 'Unhandled error in web application')
        self.assertEquals(vuln.get_url().get_file_name(), '500.py')
