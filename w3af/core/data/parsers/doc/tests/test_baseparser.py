"""
test_baseparser.py

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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse as HTTPResponse


class TestBaseParser(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')
        response = HTTPResponse(200, '', Headers(), self.url, self.url)
        self.bp_inst = BaseParser(response)

    def test_parse_blank(self):
        response = HTTPResponse(200, '', Headers(), self.url, self.url)
        bp_inst = BaseParser(response)

        self.assertRaises(NotImplementedError, bp_inst.get_comments)
        self.assertRaises(NotImplementedError, bp_inst.get_forms)
        self.assertRaises(NotImplementedError, bp_inst.get_meta_redir)
        self.assertRaises(NotImplementedError, bp_inst.get_meta_tags)
        self.assertRaises(NotImplementedError, bp_inst.get_references)
        self.assertRaises(NotImplementedError, bp_inst.get_clear_text_body)

    def test_decode_url_simple(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'latin1'

        decoded_url = bp_inst._decode_url(u'http://www.w3af.com/index.html')
        self.assertEqual(decoded_url, u'http://www.w3af.com/index.html')

    def test_decode_url_url_encoded(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'latin1'

        decoded_url = bp_inst._decode_url(u'http://www.w3af.com/ind%E9x.html')
        self.assertEqual(decoded_url, u'http://www.w3af.com/ind\xe9x.html')

    def test_decode_url_skip_safe_chars(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'latin1'

        test_url = u'http://w3af.com/search.php?a=%00x&b=2%20c=3%D1'
        expected = u'http://w3af.com/search.php?a=%00x&b=2 c=3\xd1'

        decoded_url = bp_inst._decode_url(test_url)

        self.assertEqual(decoded_url, expected)

    def test_decode_url_ignore_errors(self):
        u = URL('http://www.w3af.com/')
        response = HTTPResponse(200, u'', Headers(), u, u, charset='latin1')
        bp_inst = BaseParser(response)
        bp_inst._encoding = 'utf-8'

        test_url = u'http://w3af.com/blah.jsp?p=SQU-300&bgc=%FFAAAA'
        expected = u'http://w3af.com/blah.jsp?p=SQU-300&bgc=AAAA'

        decoded_url = bp_inst._decode_url(test_url)

        self.assertEqual(decoded_url, expected)
