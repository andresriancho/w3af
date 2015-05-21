"""
test_sed.py

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

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.mangle.sed import sed


class TestSed(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        self.plugin = sed()
        self.url = URL('http://www.w3af.com/')
        self.request = HTTPRequest(self.url)

    def tearDown(self):
        self.plugin.end()

    def test_blank_body(self):
        body = ''
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)

        option_list = self.plugin.get_options()
        option_list['expressions'].set_value('qh/User/NotLuser/')        
        self.plugin.set_options(option_list)
        
        mod_request = self.plugin.mangle_request(self.request)
        mod_response = self.plugin.mangle_response(response)
        
        self.assertEqual(mod_request.get_headers(), self.request.get_headers())
        self.assertEqual(mod_response.get_headers(), response.get_headers())

        self.assertEqual(mod_request.get_uri(), self.request.get_uri())
        self.assertEqual(mod_response.get_uri(), response.get_uri())

        self.assertEqual(mod_response.get_body(), response.get_body())

    def test_response_body(self):
        body = 'hello user!'
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, self.url, self.url, _id=1)

        option_list = self.plugin.get_options()
        option_list['expressions'].set_value('sb/user/notluser/')        
        self.plugin.set_options(option_list)
        
        mod_request = self.plugin.mangle_request(self.request)
        mod_response = self.plugin.mangle_response(response)
        
        self.assertEqual(mod_request.get_headers(), self.request.get_headers())
        self.assertEqual(mod_response.get_headers(), response.get_headers())

        self.assertEqual(mod_request.get_uri(), self.request.get_uri())
        self.assertEqual(mod_response.get_uri(), response.get_uri())

        self.assertEqual(mod_response.get_body(), 'hello notluser!')

    def test_request_headers(self):
        headers = Headers([('content-type', 'text/html')])
        request = HTTPRequest(self.url, headers=headers)

        option_list = self.plugin.get_options()
        option_list['expressions'].set_value('qh/html/xml/')        
        self.plugin.set_options(option_list)
        
        mod_request = self.plugin.mangle_request(request)
        
        value, _ = mod_request.get_headers().iget('content-type')
        self.assertEqual(value, 'text/xml')

        self.assertIs(mod_request, request)
