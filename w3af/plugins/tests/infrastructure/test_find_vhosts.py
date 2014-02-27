"""
test_find_vhosts.py

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


class TestFindVhosts(PluginTest):

    dead_link_url = 'http://moth/w3af/infrastructure/find_vhost/internal_domain.html'
    simple_url = 'http://moth/'

    _run_configs = {
        'cfg': {
        'target': None,
        'plugins': {'infrastructure': (PluginConfig('find_vhosts'),)}
        }
    }

    @attr('ci_fails')
    def test_find_vhosts(self):
        cfg = self._run_configs['cfg']
        self._scan(self.simple_url, cfg['plugins'])

        infos = self.kb.get('find_vhosts', 'find_vhosts')
        self.assertEqual(len(infos), 1, infos)

        info = infos[0]
        self.assertEqual('Virtual host identified', info.get_name())
        self.assertTrue('the virtual host name is: "intranet"' in info.get_desc(), info.get_desc())

    @attr('ci_fails')
    def test_find_vhost_dead_link(self):
        cfg = self._run_configs['cfg']
        self._scan(self.dead_link_url, cfg['plugins'])

        infos = self.kb.get('find_vhosts', 'find_vhosts')
        self.assertEqual(len(infos), 2, infos)

        expected = set(['Internal hostname in HTML link', 'Virtual host identified'])
        self.assertEqual(expected,
                         set([i.get_name() for i in infos]))