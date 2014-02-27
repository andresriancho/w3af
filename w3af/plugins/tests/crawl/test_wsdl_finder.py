"""
test_wsdl_finder.py

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


class TestWSDLFinder(PluginTest):

    base_url = 'http://moth/w3af/crawl/wsdl_finder/'

    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('wsdl_finder'),
                                  PluginConfig('web_spider',
                                               (
                                               'only_forward', True, PluginConfig.BOOL))),
                        }
        }
    }

    @attr('ci_fails')
    def test_wsdl_found(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('wsdl_greper', 'wsdl')

        self.assertEqual(len(infos), 1, infos)

        info = infos[0]

        self.assertIn('WSDL resource', info.get_name())
        self.assertEquals(info.get_url().url_string,
                          self.base_url + 'web_service_server.php')