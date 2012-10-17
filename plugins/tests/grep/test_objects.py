'''
test_feeds.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import unittest

import core.data.kb.knowledgeBase as kb

from plugins.grep.objects import objects
from core.data.url.HTTPResponse import HTTPResponse
from core.data.request.fuzzable_request import FuzzableRequest
from core.data.parsers.urlParser import url_object


class test_objects(unittest.TestCase):
    
    def setUp(self):
        self.plugin = objects()

        from core.controllers.core_helpers.fingerprint_404 import fingerprint_404_singleton
        from core.data.url.xUrllib import xUrllib
        f = fingerprint_404_singleton( [False, False, False] )
        f.set_url_opener( xUrllib() )
        kb.kb.save('objects', 'objects', [])

    def tearDown(self):
        self.plugin.end()
                
    def test_object(self):
        body = '''header
        <OBJECT 
          classid="clsid:8AD9C840-044E-11D1-B3E9-00805F499D93"
          width="200" height="200">
          <PARAM name="code" value="Applet1.class">
        </OBJECT>        
        footer'''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        
        self.assertEquals( len(kb.kb.get('objects', 'object')), 1 )
        i = kb.kb.get('objects', 'object')[0]
        self.assertTrue( '"object"' in i.getDesc() )
            
    def test_applet(self):
        body = '''header
        <APPLET code="XYZApp.class" codebase="html/" align="baseline"
            width="200" height="200">
            <PARAM name="model" value="models/HyaluronicAcid.xyz">
            No Java 2 SDK, Standard Edition v 1.4.2 support for APPLET!!
        </APPLET>        
        footer'''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        
        self.assertEquals( len(kb.kb.get('objects', 'applet')), 1 )
        i = kb.kb.get('objects', 'applet')[0]
        self.assertTrue( '"applet"' in i.getDesc() )

    def test_none(self):
        body = '<an object="1"> <or applet=2> <apple>'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = HTTPResponse(200, body , headers, url, url)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        
        self.assertEquals( len(kb.kb.get('objects', 'objects')), 0 )
    
