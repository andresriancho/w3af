# -*- coding: UTF-8 -*-
"""
test_swf.py

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
import os

from w3af import ROOT_PATH
from w3af.core.data.parsers.swf import SWFParser
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.url import URL


class TestSWFParser(unittest.TestCase):
    
    WIVET_SAMPLE = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'tests',
                                'data', 'wivet1.swf')
    DEMO_SAMPLE = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'tests',
                               'data', 'subscribe.swf')
    
    def parse(self, filename):
        body = file(filename).read()
        swf_mime = 'application/x-shockwave-flash'
        hdrs = Headers({'Content-Type': swf_mime}.items())
        response = HTTPResponse(200, body, hdrs,
                                URL('http://moth/xyz/'),
                                URL('http://moth/xyz/'),
                                _id=1)
        
        parser = SWFParser(response)
        return parser
    
    def test_swf_parser_wivet(self):
        parser = self.parse(self.WIVET_SAMPLE)
        parsed, re_refs = parser.get_references()
        
        expected = set([URL('http://moth/innerpages/19_1f52a.php'),
                        URL('http://purl.org/dc/elements/1.1'),
                        URL('http://www.adobe.com/products/flex'),
                        URL('http://www.w3.org/1999/02/22-rdf-syntax-ns')])
        
        self.assertEqual(parsed, [])
        self.assertEqual(set(re_refs), expected)
        
    def test_swf_parser_subscribe(self):
        parser = self.parse(self.DEMO_SAMPLE)
        parsed, re_refs = parser.get_references()
        
        expected = set([URL('http://moth/xyz/subscribe.aspx'),])
        
        self.assertEqual(parsed, [])
        self.assertEqual(set(re_refs), expected)
        
