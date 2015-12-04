"""
test_form_autocomplete.py

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.grep.form_autocomplete import form_autocomplete


class TestFormAutocomplete(PluginTest):

    target_url = get_moth_http('/grep/form_autocomplete/')

    _run_configs = {
        'cfg1': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('form_autocomplete'),),
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
        vulns = self.kb.get('form_autocomplete', 'form_autocomplete')

        expected_results = ['form-default.html',
                            'form-on.html',
                            'form-on-field-on.html',
                            'form-two-fields.html']

        filenames = [vuln.get_url().get_file_name() for vuln in vulns]
        filenames.sort()
        expected_results.sort()

        self.assertEquals(expected_results, filenames)


class TestFormAutocompleteRaw(unittest.TestCase):
    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = form_autocomplete()

    def tearDown(self):
        kb.kb.cleanup()

    def test_form_autocomplete_group_info_set(self):
        body = '<form action="/login"><input type="password" name="p"></form>'
        url_1 = URL('http://www.w3af.com/1')
        url_2 = URL('http://www.w3af.com/2')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url_1, method='GET')
        resp_1 = HTTPResponse(200, body, headers, url_1, url_1, _id=1)
        resp_2 = HTTPResponse(200, body, headers, url_2, url_2, _id=1)

        self.plugin.grep(request, resp_1)
        self.plugin.grep(request, resp_2)
        self.plugin.end()

        expected_desc = (u'The application contains 2 different URLs with a'
                         u' <form> element which has auto-complete enabled'
                         u' for password fields. The first two vulnerable'
                         u' URLs are:\n'
                         u' - http://www.w3af.com/2\n'
                         u' - http://www.w3af.com/1\n')

        # pylint: disable=E1103
        info_set = kb.kb.get_one('form_autocomplete', 'form_autocomplete')
        self.assertEqual(set(info_set.get_urls()), {url_1, url_2})
        self.assertEqual(info_set.get_desc(), expected_desc)
        # pylint: enable=E1103