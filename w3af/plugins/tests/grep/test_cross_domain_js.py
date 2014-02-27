"""
test_cross_domain_js.py

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


@attr('smoke')
@attr('ci_ready')
class TestCrossDomainJS(PluginTest):

    target_url = get_moth_http('/grep/cross_domain_js/')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('cross_domain_js'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),)
            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('cross_domain_js', 'cross_domain_js')
        self.assertEquals(3, len(infos), infos)

        EXPECTED = set(['cross_domain_script_mixed.html',
                        'cross_domain_script_with_type.html',
                        'cross_domain_script.html'])
        found_fnames = set([i.get_url().get_file_name() for i in infos])

        self.assertEquals(EXPECTED,
                          found_fnames)
