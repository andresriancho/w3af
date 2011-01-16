'''
test_codeDisclosure.py

Copyright 2011 Andres Riancho

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

from plugins.grep.codeDisclosure import codeDisclosure
import unittest

from core.data.url.httpResponse import httpResponse
from core.data.request.fuzzableRequest import fuzzableRequest
from core.data.parsers.urlParser import url_object
import core.data.kb.knowledgeBase as kb


class test_codeDisclosure(unittest.TestCase):
    
    def setUp(self):
        self.plugin = codeDisclosure()

        from core.controllers.coreHelpers.fingerprint_404 import fingerprint_404
        from core.data.url.xUrllib import xUrllib
        xurllib = xUrllib()
        fingerprint_404( xurllib )
        from core.controllers.coreHelpers.fingerprint_404 import is_404
        is_404 = lambda x: True

        
    def test_ASP_code_disclosure(self):
        body = 'header <% Response.Write("Hello World!") %> footer'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest()
        request.setURL( url )
        request.setMethod( 'GET' )
        self.plugin.grep(request, response)
        self.assertTrue( len(kb.kb.getData('codeDisclosure', 'codeDisclosure')) == 1 )
            
    def test_PHP_code_disclosure(self):
        body = 'header <? echo $a; ?> footer'
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest()
        request.setURL( url )
        request.setMethod( 'GET' )
        self.plugin.grep(request, response)
        self.assertTrue( len(kb.kb.getData('codeDisclosure', 'codeDisclosure')) == 1 )


    def test_no_code_disclosure_blank(self):
        body = ''
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, url, url)
        request = fuzzableRequest()
        request.setURL( url )
        request.setMethod( 'GET' )
        self.plugin.grep(request, response)
        self.assertTrue( len(kb.kb.getData('codeDisclosure', 'codeDisclosure')) == 0 )

    def test_no_code_disclosure(self):
        self.assertTrue( True )
    
    def test_no_code_disclosure_xml(self):
        self.assertTrue( True )

if __name__ == "__main__":
    unittest.main()
