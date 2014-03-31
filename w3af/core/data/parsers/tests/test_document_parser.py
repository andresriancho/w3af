# -*- coding: UTF-8 -*-
"""
test_sgmlparsers.py

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

from nose.plugins.skip import SkipTest

from w3af import ROOT_PATH
from w3af.core.data.parsers.url import URL
from w3af.core.data.parsers.document_parser import document_parser_factory, DocumentParser
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.html import HTMLParser
from w3af.core.data.parsers.pdf import PDFParser
from w3af.core.controllers.exceptions import BaseFrameworkException


def _build_http_response(body_content, content_type):
    headers = Headers()
    headers[u'content-type'] = content_type

    url = URL('http://w3af.com')

    return HTTPResponse(200, body_content, headers, url, url, charset='utf-8')


class TestDocumentParserFactory(unittest.TestCase):

    PDF_FILE = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'tests',
                            'data', 'links.pdf')
    
    HTML_FILE = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'tests',
                             'data', 'sharepoint-pl.html')

    def test_html(self):
        parser = document_parser_factory(_build_http_response('', u'text/html'))

        self.assertIsInstance(parser, DocumentParser)
        self.assertIsInstance(parser._parser, HTMLParser)

    def test_pdf_case01(self):
        parser = document_parser_factory(
            _build_http_response(file(self.PDF_FILE).read(),
                                 u'application/pdf'))

        self.assertIsInstance(parser, DocumentParser)
        self.assertIsInstance(parser._parser, PDFParser)

    def test_no_parser(self):
        response = _build_http_response('%!23', u'application/bar')
        self.assertRaises(BaseFrameworkException, document_parser_factory, response)

    def test_no_parser_binary(self):
        all_chars = ''.join([chr(i) for i in xrange(0,255)])
        response = _build_http_response(all_chars, u'application/bar')
        self.assertRaises(BaseFrameworkException, document_parser_factory, response)
        
    def test_issue_106_invalid_url(self):
        """
        Issue to verify https://github.com/andresriancho/w3af/issues/106
        """
        sharepoint_pl = file(self.HTML_FILE).read()
        parser = document_parser_factory(_build_http_response(sharepoint_pl,
                                                              u'text/html'))

        self.assertIsInstance(parser, DocumentParser)
        self.assertIsInstance(parser._parser, HTMLParser)
        
        paths = []
        paths.extend(url.get_path_qs() for url in parser.get_references()[0])
        paths.extend(url.get_path_qs() for url in parser.get_references()[1])
        
        expected_paths = set(['/szukaj/_vti_bin/search.asmx',
                              '/_vti_bin/search.asmx?disco=',
                              '/_vti_bin/search.asmx',
                              '/2003/05/soap-envelope',
                              '/soap/envelope/',
                              '/2001/XMLSchema',
                              '/2001/XMLSchema-instance'])
        
        self.assertEqual(expected_paths, set(paths))
        