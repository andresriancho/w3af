"""
test_memcachei.py

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
from w3af.core.controllers.ci.moth import get_moth_http


class TestMemcachei(PluginTest):

    target_url = get_moth_http('/audit/memcache_injection/memcache_value.py')

    _run_configs = {
        'cfg': {
            'target': target_url + '?key=x',
            'plugins': {
                'audit': (PluginConfig('memcachei'),),
            }
        }
    }

    def test_found_memcachei(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('memcachei', 'memcachei')
        self.assertEquals(1, len(vulns))
        vuln = vulns[0]

        # Now some tests around specific details of the found vuln
        self.assertEquals('Memcache injection vulnerability', vuln.get_name())
        self.assertEquals(self.target_url, str(vuln.get_url()))
