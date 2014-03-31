"""
test_dot_net_errors.py

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


class TestDotNetErrors(PluginTest):

    moth_url = 'http://moth/w3af/infrastructure/dot_net_errors/'

    _run_configs = {
        'cfg': {
            'target': moth_url,
            'plugins': {'infrastructure': (PluginConfig('dot_net_errors'),),
                        'crawl': (PluginConfig('web_spider',
                                               ('only_forward', True, PluginConfig.BOOL),),)}
        }
    }

    @attr('ci_fails')
    def test_dot_net_errors(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('dot_net_errors', 'dot_net_errors')

        self.assertEqual(len(infos), 1, infos)

        info = infos[0]

        self.assertEqual(
            info.get_name(), 'Information disclosure via .NET errors')