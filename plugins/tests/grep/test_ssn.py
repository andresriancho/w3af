'''
test_ssn.py

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

from core.data.url.httpResponse import httpResponse
from core.data.request.fuzzableRequest import fuzzableRequest
from core.data.parsers.urlParser import url_object
from plugins.grep.ssn import ssn


class test_ssn(unittest.TestCase):
    
    def setUp(self):
        kb.kb.cleanup()
        self.plugin = ssn()
        self.plugin._already_inspected = set()        
        self.url = url_object('http://www.w3af.com/')
        self.request = fuzzableRequest(self.url)
         
    def test_ssn_empty_string(self):
        body = ''
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, self.url, self.url)
        self.plugin._already_inspected = set()
        self.plugin.grep(self.request, response)
        self.assertEquals( len(kb.kb.getData('ssn', 'ssn')) , 0 )
        
    def test_ssn_separated(self):
        body = 'header 771-12-9876 footer'
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, self.url, self.url)
        self.plugin.grep(self.request, response)
        self.assertEqual( len(kb.kb.getData('ssn', 'ssn')) , 1 )
    
    def test_ssn_with_html(self):
        self.plugin._already_inspected = set()
        body = 'header <b>771</b>-<b>12</b>-<b>9876</b> footer'
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, self.url, self.url)
        self.plugin.grep(self.request, response)
        self.assertEqual( len(kb.kb.getData('ssn', 'ssn')) , 1 )
    
    def test_ssn_together(self):
        body = 'header 771129876 footer'
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, self.url, self.url)
        self.plugin.grep(self.request, response)
        self.assertEquals( len(kb.kb.getData('ssn', 'ssn')) , 1 )
    
    def test_ssn_extra_number(self): 
        body = 'header 7711298761 footer'
        headers = {'content-type': 'text/html'}
        response = httpResponse(200, body , headers, self.url, self.url)
        self.plugin.grep(self.request, response)
        self.assertEqual( len(kb.kb.getData('ssn', 'ssn')), 0 )
    
    def test_find_ssn(self):
        EXPECTED = set( [(None, None),
                         ('771129876', '771-12-9876'),
                         ('771129876', '771-12-9876'),
                         ('771 12 9876', '771-12-9876'),
                         ('771 12 9876', '771-12-9876'),
                         ('771 12 9876', '771-12-9876'),
                         ('771129876', '771-12-9876') ] )
        
        res = []
        res.append( self.plugin._find_SSN( '' ) )
        res.append( self.plugin._find_SSN( 'header 771129876 footer' ) )
        res.append( self.plugin._find_SSN( '771129876' ) )
        res.append( self.plugin._find_SSN( 'header 771 12 9876 footer' ) )
        res.append( self.plugin._find_SSN( 'header 771 12 9876 32 footer' ) )
        res.append( self.plugin._find_SSN( 'header 771 12 9876 32 64 footer' ) )
        res.append( self.plugin._find_SSN( 'header 771129876 771129875 footer' ) )
        
        self.assertEqual( EXPECTED,
                          set(res) )