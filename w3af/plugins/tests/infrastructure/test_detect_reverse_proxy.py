"""
test_detect_reverse_proxy.py

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


class TestDetectReverseProxy(PluginTest):

    proxied_url = 'http://moth/w3af/infrastructure/detect_reverse_proxy/'
    simple_url = 'http://moth/'

    _run_configs = {
        'cfg': {
        'target': None,
        'plugins': {'infrastructure': (PluginConfig('detect_reverse_proxy'),)}
        }
    }

    @attr('ci_fails')
    def test_detect_reverse_proxy(self):
        cfg = self._run_configs['cfg']
        self._scan(self.proxied_url, cfg['plugins'])

        infos = self.kb.get('detect_reverse_proxy', 'detect_reverse_proxy')
        self.assertEqual(len(infos), 1, infos)

        info = infos[0]
        self.assertEqual('Reverse proxy identified', info.get_name())

    @attr('ci_fails')
    def test_not_detect_reverse_proxy(self):
        cfg = self._run_configs['cfg']
        self._scan(self.simple_url, cfg['plugins'])

        infos = self.kb.get('detect_reverse_proxy', 'detect_reverse_proxy')
        self.assertEqual(len(infos), 0, infos)