# -*- coding: UTF-8 -*-
"""
test_pdf.py

Copyright 2011 Andres Riancho

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
from w3af.core.data.parsers.doc.pdf import pdf_to_text, PDFParser
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL


class TestPDF(unittest.TestCase):
    
    SIMPLE_SAMPLE = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc',
                                 'tests', 'data', 'simple.pdf')
    LINKS_SAMPLE = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc',
                                'tests', 'data', 'links.pdf')
    
    def test_pdf_to_text(self):
        text = pdf_to_text(file(self.SIMPLE_SAMPLE).read())
        self.assertIn('Hello', text)
        self.assertIn('World', text)

    def test_pdf_to_text_no_pdf(self):
        text = pdf_to_text('hello world')
        self.assertEqual('', text)
    
    def test_pdf_parser(self):
        body = file(self.LINKS_SAMPLE).read()
        hdrs = Headers({'Content-Type': 'application/pdf'}.items())
        response = HTTPResponse(200, body, hdrs,
                                URL('http://moth/'),
                                URL('http://moth/'),
                                _id=1)        
        
        parser = PDFParser(response)
        parser.parse()
        parsed, re_refs = parser.get_references()
        
        self.assertEqual(parsed, [])
        self.assertEqual(re_refs, [URL('http://moth/pdf/')])
        self.assertEqual(parser.get_clear_text_body().strip(),
                         'http://moth/pdf/')
