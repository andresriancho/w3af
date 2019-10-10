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
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.plugins.grep.strange_parameters import strange_parameters


class TestStrangeParameters(unittest.TestCase):

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
        body = ('<html>'
                '<a href="http://moth/abc.jsp?sql=SELECT x FROM TABLE">x</a>'
                '</html>')
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 1)

    def test_multi(self):
        body = """<html>
                  <a href="http://moth/abc.jsp?sql=SELECT x FROM TABLE">x</a>
                  <a href="http://moth/abc.jsp?call=s(12,3)">x</a>
                  </html>"""
        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        vulns = kb.kb.get('strange_parameters', 'strange_parameters')
        self.assertEquals(len(vulns), 2, vulns)

    def test_strange_parameters_sent_false_positive_01(self):
        body = ('<link rel="amphtml" href="http://w3af.org/?searchsubmit='
                'S%C3%B6k&#038;s=echo+str_repeat%28%27ruvkt%27%2C5%29%3B&#038;amp">')

        url = URL('http://w3af.org/?searchsubmit=S%C3%B6k&s=echo%20str_repeat%28%27ruvkt%27%2C5%29%3B')
        response = HTTPResponse(200, body, self.headers, url, url, _id=1)

        request = FuzzableRequest(url)

        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 0)

    def test_strange_parameters_sent_false_positive_02(self):
        body = '<a href="http://news.google.se/news/url?url=http%3A%2F%2Fwww.foo.com%2F">xyz</a>'

        response = HTTPResponse(200, body, self.headers, self.url, self.url, _id=1)
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_parameters',
                                        'strange_parameters')), 0)

