"""
test_ajax.py

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
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.grep.ajax import ajax


class test_ajax(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = ajax()
        self.url = URL('http://www.w3af.com/')
        self.request = FuzzableRequest(self.url)
        kb.kb.clear('ajax', 'ajax')

    def tearDown(self):
        self.plugin.end()

    def test_ajax_empty(self):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('ajax', 'ajax')), 0)

    def test_ajax_find(self):
        body = '<html><head><script>xhr = new XMLHttpRequest(); xhr.open(GET, "data.txt",  true); </script></head><html>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('ajax', 'ajax')), 1)

    def test_ajax_broken_html(self):
        body = '<html><head><script>xhr = new XMLHttpRequest(); xhr.open(GET, "data.txt",  true); </head><html>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('ajax', 'ajax')), 1)

    def test_ajax_broken_2(self):
        body = '<html><head><script>xhr = new XMLHttpRequest(); xhr.open(GET, "data.txt",  true);'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('ajax', 'ajax')), 1)

    def test_ajax_find_2(self):
        body = '<html><head><script> ... xhr = new ActiveXObject("Microsoft.XMLHTTP"); ... </script></head><html>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('ajax', 'ajax')), 1)

    def test_ajax_two(self):
        body = '<script> ... xhr = new XMLHttpRequest(); ... xhr = new ActiveXObject("Microsoft.XMLHTTP"); ... </script>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('ajax', 'ajax')), 1)
