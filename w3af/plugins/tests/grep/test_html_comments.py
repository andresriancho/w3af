"""
test_html_comments.py

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
class TestHTMLComments(PluginTest):

    html_comments_url = get_moth_http('/grep/html_comments/')

    _run_configs = {
        'cfg1': {
            'target': html_comments_url,
            'plugins': {
                'grep': (PluginConfig('html_comments'),),
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

        infos_html = self.kb.get('html_comments', 'html_comment_hides_html')
        infos_interesting = self.kb.get('html_comments',
                                        'interesting_comments')

        self.assertEquals(1, len(infos_html), infos_html)
        self.assertEquals(1, len(infos_interesting), infos_interesting)

        html_info = infos_html[0]
        interesting_info = infos_interesting[0]

        self.assertEqual(interesting_info.get_name(), 'Interesting HTML comment')
        self.assertEqual(html_info.get_name(), 'HTML comment contains HTML code')
