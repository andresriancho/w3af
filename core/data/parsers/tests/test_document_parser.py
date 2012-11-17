# -*- coding: UTF-8 -*-
'''
test_sgmlparsers.py

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
import unittest

from nose.plugins.skip import SkipTest

from core.data.parsers.url import URL
from core.data.parsers.document_parser import document_parser_factory, DocumentParser
from core.data.url.HTTPResponse import HTTPResponse
from core.data.dc.headers import Headers
from core.data.parsers.htmlParser import HTMLParser
from core.data.parsers.pdf import PDFParser
from core.controllers.exceptions import w3afException


def _build_http_response(body_content, content_type):
    headers = Headers()
    headers['content-type'] = content_type

    url = URL('http://w3af.com')

    return HTTPResponse(200, body_content, headers, url, url, charset='utf-8')


class TestDocumentParserFactory(unittest.TestCase):

    def test_html(self):
        parser = document_parser_factory(_build_http_response('', 'text/html'))

        self.assertIsInstance(parser, DocumentParser)
        self.assertIsInstance(parser._parser, HTMLParser)

    def test_pdf(self):
        raise SkipTest('Need to define an example PDF file that doesnt break'
                       ' the pypdf parser.')
        parser = document_parser_factory(
            _build_http_response('%PDF-\n1\n%%EOF',
                                 'application/pdf'))

        self.assertIsInstance(parser, DocumentParser)
        self.assertIsInstance(parser._parser, PDFParser)

    def test_no_parser(self):
        response = _build_http_response('%!23', 'application/bar')
        self.assertRaises(w3afException, document_parser_factory, response)
