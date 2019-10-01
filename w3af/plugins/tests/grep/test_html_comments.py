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
import unittest

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.grep.html_comments import html_comments

from nose.plugins.attrib import attr
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


@attr('smoke')
@attr('ci_ready')
class TestHTMLCommentsIntegration(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body=('<!-- secret password123 -->'
                                         '<!-- <a href="/x"></a> -->'),
                                   method='GET',
                                   status=200)]

    _run_configs = {
        'cfg1': {
            'target': target_url,
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


class TestHTMLCommentsUnit(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = html_comments()

    def tearDown(self):
        self.plugin.end()

    def test_html_comment(self):
        body = '<!-- secret password123 -->'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')

        response = HTTPResponse(200, body, headers, url, url, _id=1)
        self.plugin.grep(request, response)

        info_sets = kb.kb.get('html_comments', 'interesting_comments')
        self.assertEquals(len(info_sets), 1)

    def test_html_comment_profiling(self):
        body = '<!-- secret password123 -->'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')

        response = HTTPResponse(200, body, headers, url, url, _id=1)

        for _ in xrange(500):
            self.plugin.grep(request, response)

        info_sets = kb.kb.get('html_comments', 'interesting_comments')
        self.assertEquals(len(info_sets), 1)
