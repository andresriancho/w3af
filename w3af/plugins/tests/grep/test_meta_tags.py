"""
test_meta_tags.py

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

import w3af.core.data.constants.severity as severity


@attr('ci_ready')
class TestMetaTags(PluginTest):

    meta_tags_url = get_moth_http('/grep/meta_tags/')

    _run_configs = {
        'cfg1': {
            'target': meta_tags_url,
            'plugins': {
                'grep': (PluginConfig('meta_tags'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('meta_tags', 'meta_tags')

        self.assertEquals(2, len(vulns))

        self.assertEquals(set([severity.INFORMATION] * 2),
                          set([v.get_severity() for v in vulns]))

        self.assertEquals(set(['Interesting META tag'] * 2),
                          set([v.get_name() for v in vulns]))

        joined_desc = ''.join([v.get_desc() for v in vulns])

        self.assertTrue('linux' in joined_desc)
        self.assertTrue('Google Sitemap' in joined_desc)
