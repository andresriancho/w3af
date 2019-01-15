"""
test_expect_ct.py

Copyright 2019 Andres Riancho

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
from w3af.plugins.grep.expect_ct import expect_ct


class TestECTSecurity(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        self.plugin = expect_ct()

    def tearDown(self):
        self.plugin.end()
        kb.kb.cleanup()

    def test_http_no_vuln(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)
        self.assertEquals(len(kb.kb.get('expect_ct',
                                        'expect_ct')), 0)

    def test_https_with_ect(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html'),
                           ('expect-ct',
                            'max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)
        self.assertEquals(len(kb.kb.get('expect_ct',
                                        'expect_ct')), 0)

    def test_https_without_ect(self):
        body = ''
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)

        findings = kb.kb.get('expect_ct',
                             'expect_ct')
        self.assertEquals(len(findings), 1, findings)

        info_set = findings[0]
        expected_desc = u'The remote web server sent 1 HTTPS responses which' \
                        u' do not contain the Strict-Transport-Security' \
                        u' header. The first ten URLs which did not send the' \
                        u' header are:\n - https://www.w3af.com/\n'

        self.assertEqual(info_set.get_id(), [1])
        self.assertEqual(info_set.get_desc(), expected_desc)
        self.assertEqual(info_set.get_name(),
                         'Missing Expect-CT header')

    def test_https_without_ect_group_by_domain(self):
        body = ''
        url = URL('https://www.w3af.com/1')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)

        body = ''
        url = URL('https://www.w3af.com/2')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=2)

        self.plugin.grep(request, resp)

        findings = kb.kb.get('expect_ct',
                             'expect_ct')
        self.assertEquals(len(findings), 1, findings)

        info_set = findings[0]
        expected_desc = u'The remote web server sent 2 HTTPS responses which' \
                        u' do not contain the Expect-CT' \
                        u' header. The first ten URLs which did not send the' \
                        u' header are:\n - https://www.w3af.com/1\n' \
                        u' - https://www.w3af.com/2\n'

        self.assertEqual(info_set.get_id(), [1, 2])
        self.assertEqual(info_set.get_desc(), expected_desc)
        self.assertEqual(info_set.get_name(),
                         'Missing Expect-CT header')
