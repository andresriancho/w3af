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
import unittest
from itertools import repeat

from mock import patch

import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.grep.meta_tags import meta_tags


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

        self.assertIn('linux', joined_desc)
        self.assertIn('verify-v1', joined_desc)


class TestMetaTagsRaw(unittest.TestCase):
    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = meta_tags()

    def tearDown(self):
        kb.kb.cleanup()

    @patch('w3af.plugins.grep.meta_tags.is_404', side_effect=repeat(False))
    def test_meta_user(self, *args):
        body = '<meta test="user/pass"></script>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)
        self.plugin.end()

        infos = kb.kb.get('meta_tags', 'meta_tags')
        self.assertEquals(len(infos), 1)

        info = infos[0]
        self.assertEqual(info.get_name(), 'Interesting META tag')
        self.assertIn('pass', info.get_desc())

    @patch('w3af.plugins.grep.meta_tags.is_404', side_effect=repeat(False))
    def test_group_info_set(self, *args):
        body = '<meta test="user/pass"></script>'
        url_1 = URL('http://www.w3af.com/1')
        url_2 = URL('http://www.w3af.com/2')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url_1, method='GET')
        resp_1 = HTTPResponse(200, body, headers, url_1, url_1, _id=1)
        resp_2 = HTTPResponse(200, body, headers, url_2, url_2, _id=1)

        self.plugin.grep(request, resp_1)
        self.plugin.grep(request, resp_2)
        self.plugin.end()

        expected_desc = u'The application sent a <meta> tag with the' \
                        u' attribute value set to "user/pass" which looks' \
                        u' interesting and should be manually reviewed. The' \
                        u' first ten URLs which sent the tag are:\n' \
                        u' - http://www.w3af.com/2\n' \
                        u' - http://www.w3af.com/1\n'

        # pylint: disable=E1103
        info_set = kb.kb.get_one('meta_tags', 'meta_tags')
        self.assertEqual(set(info_set.get_urls()), {url_1, url_2})
        self.assertEqual(info_set.get_desc(), expected_desc)
        # pylint: enable=E1103