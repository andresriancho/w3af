"""
test_user_defined_regex.py

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
from w3af.plugins.grep.user_defined_regex import user_defined_regex


class test_user_defined_regex(unittest.TestCase):

    def setUp(self):
        self.plugin = user_defined_regex()

    def test_user_defined_regex(self):
        body = '<html><head><script>xhr = new XMLHttpRequest(); xhr.open(GET, "data.txt",  true);'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        options = self.plugin.get_options()
        options['single_regex'].set_value('".*?"')
        self.plugin.set_options(options)

        self.plugin.grep(request, response)
        self.assertEquals(
            len(kb.kb.get('user_defined_regex', 'user_defined_regex')), 1)

        info_obj = kb.kb.get('user_defined_regex', 'user_defined_regex')[0]
        self.assertTrue(info_obj.get_desc(
        ).startswith('User defined regular expression "'))
        self.assertIn('data.txt', info_obj.get_desc())

    def tearDown(self):
        self.plugin.end()
