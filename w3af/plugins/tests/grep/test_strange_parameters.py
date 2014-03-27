"""
test_strange_parameters.py

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
from w3af.plugins.grep.strange_parameters import strange_parameters


class test_strange_parameters(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        self.plugin = strange_parameters()
        self.url = URL('http://www.w3af.com/')
        self.headers = Headers([('content-type', 'text/html')])
        self.request = FuzzableRequest(self.url)

    def tearDown(self):
        self.plugin.end()

    def test_strange_parameters_empty(self):
        body = ''
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 0)

    def test_strange_parameters_not_find_1(self):
        body = '<html><a href="/?id=3">x</a></html>'
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 0)

    def test_strange_parameters_not_find_2(self):
        body = '<html><a href="/?id=3&id=3&id=5&foo=bar">x</a></html>'
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 0)

    def test_strange_parameters_not_find_3(self):
        body = '<html><a href="http://moth/abc.jsp?id=3&id=3&id=5&foo=bar">x</a></html>'
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 0)

    def test_strange_parameters_find(self):
        body = '<html><a href="http://moth/abc.jsp?call=s(12,3)">x</a></html>'
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 1)

    def test_strange_parameters_find_sql(self):
        body = '<html><a href="http://moth/abc.jsp?call=SELECT x FROM TABLE">x</a></html>'
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 1)

    def test_multi(self):
        body = """<html>
                  <a href="http://moth/abc.jsp?call=SELECT x FROM TABLE">x</a>
                  <a href="http://moth/abc.jsp?call=s(12,3)">x</a>
                  </html>"""
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 2)
