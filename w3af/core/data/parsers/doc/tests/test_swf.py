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
from w3af.core.data.parsers.doc.swf import SWFParser
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL


class TestSWFParser(unittest.TestCase):

    SAMPLE_DIR = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc',
                              'tests', 'data')

    WIVET_SAMPLE = os.path.join(SAMPLE_DIR, 'wivet1.swf')
    DEMO_SAMPLE = os.path.join(SAMPLE_DIR, 'subscribe.swf')
    DOMAIN_DECODE_1 = os.path.join(SAMPLE_DIR, 'test-5925-1.swf')
    DOMAIN_DECODE_2 = os.path.join(SAMPLE_DIR, 'test-5925-2.swf')
    
    def parse(self, filename):
        body = file(filename).read()
        swf_mime = 'application/x-shockwave-flash'
        hdrs = Headers({'Content-Type': swf_mime}.items())
        response = HTTPResponse(200, body, hdrs,
                                URL('http://moth/xyz/'),
                                URL('http://moth/xyz/'),
                                _id=1)
        
        parser = SWFParser(response)
        parser.parse()
        return parser
    
    def test_swf_parser_wivet(self):
        parser = self.parse(self.WIVET_SAMPLE)
        parsed, re_refs = parser.get_references()
        
        expected = {URL('http://moth/innerpages/19_1f52a.php'),
                    URL('http://purl.org/dc/elements/1.1'),
                    URL('http://www.adobe.com/products/flex'),
                    URL('http://www.w3.org/1999/02/22-rdf-syntax-ns')}
        
        self.assertEqual(parsed, [])
        self.assertEqual(set(re_refs), expected)
        
    def test_swf_parser_subscribe(self):
        parser = self.parse(self.DEMO_SAMPLE)
        parsed, re_refs = parser.get_references()
        
        expected = {URL('http://moth/xyz/subscribe.aspx')}
        
        self.assertEqual(parsed, [])
        self.assertEqual(set(re_refs), expected)

    def test_swf_parser_domain_encoding_1(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/5682
        """
        parser = self.parse(self.DOMAIN_DECODE_1)
        parsed, re_refs = parser.get_references()

        self.assertEqual(parsed, [])
        self.assertEqual(len(set(re_refs)), 1)

        url = re_refs[0]
        self.assertIsInstance(url.get_domain(), str)
        self.assertIsInstance('www.adamdorman.com', str)

    def test_swf_parser_domain_encoding_2(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/5682
        """
        parser = self.parse(self.DOMAIN_DECODE_2)
        parsed, re_refs = parser.get_references()

        expected = {URL('http://mail.stiei.edu.cn/'),
                    URL('http://e-learning.stiei.edu.cn/eol/homepage/common/index_newjpk.jsp'),
                    URL('http://xxgk.stiei.edu.cn/'),
                    URL('http://portal1.stiei.edu.cn:8081/'),
                    URL('http://e-learning.stiei.edu.cn/')}

        self.assertEqual(parsed, [])
        self.assertEqual(set(re_refs), expected)
