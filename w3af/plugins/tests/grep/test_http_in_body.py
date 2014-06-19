"""
test_http_in_body.py

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig
import w3af.core.data.constants.severity as severity


class TestHttpInBody(PluginTest):

    target_url = get_moth_http('/grep/http_in_body/')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('http_in_body'),),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('http_in_body', 'request')
        self.assertEquals(1, len(infos), infos)
        
        info = infos[0]
        self.assertEquals(get_moth_http('/grep/http_in_body/http_request.html'),
                          str(info.get_url()))
        self.assertEquals(severity.INFORMATION, info.get_severity())
        self.assertEquals('HTTP Request in HTTP body', info.get_name())

        infos = self.kb.get('http_in_body', 'response')
        self.assertEquals(1, len(infos), infos)
        
        info = infos[0]
        self.assertEquals(get_moth_http('/grep/http_in_body/http_response.html'),
                          str(info.get_url()))
        self.assertEquals(severity.INFORMATION, info.get_severity())
        self.assertEquals('HTTP Response in HTTP body', info.get_name())
