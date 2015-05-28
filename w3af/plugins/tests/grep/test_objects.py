"""
test_feeds.py

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
from w3af.plugins.grep.objects import objects
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers


class test_objects(unittest.TestCase):

    def setUp(self):
        self.plugin = objects()
        kb.kb.clear('objects', 'objects')

    def tearDown(self):
        self.plugin.end()

    def test_object(self):
        body = """header
        <OBJECT
          classid="clsid:8AD9C840-044E-11D1-B3E9-00805F499D93"
          width="200" height="200">
          <PARAM name="code" value="Applet1.class">
        </OBJECT>
        footer"""
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('objects', 'object')), 1)
        i = kb.kb.get('objects', 'object')[0]
        self.assertTrue('"object"' in i.get_desc())

    def test_applet(self):
        body = """header
        <APPLET code="XYZApp.class" codebase="html/" align="baseline"
            width="200" height="200">
            <PARAM name="model" value="models/HyaluronicAcid.xyz">
            No Java 2 SDK, Standard Edition v 1.4.2 support for APPLET!!
        </APPLET>
        footer"""
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('objects', 'applet')), 1)
        i = kb.kb.get('objects', 'applet')[0]
        self.assertTrue('"applet"' in i.get_desc())

    def test_none(self):
        body = '<an object="1"> <or applet=2> <apple>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('objects', 'objects')), 0)
