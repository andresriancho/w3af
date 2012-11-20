'''
test_url.py

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

from nose.plugins.skip import SkipTest

from core.data.parsers.url import URL


class TestURLParser(unittest.TestCase):

    #
    #    Decode tests
    #
    def decode_get_qs(self, url_str):
        return URL(url_str).url_decode().querystring['id'][0]

    def test_decode_simple(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1')
        EXPECTED = '1'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_perc_20(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1%202')
        EXPECTED = u'1 2'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_space(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1 2')
        EXPECTED = u'1 2'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_plus(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1+2')
        EXPECTED = u'1+2'
        self.assertEqual(qs_value, EXPECTED)

    def test_decode_url_encode_plus(self):
        qs_value = self.decode_get_qs(
            u'https://w3af.com:443/xyz/file.asp?id=1%2B2')
        EXPECTED = u'1+2'
        self.assertEqual(qs_value, EXPECTED)

    #
    #    Encode tests
    #
    def test_encode_simple(self):
        res_str = URL(u'http://w3af.com').url_encode()
        EXPECTED = 'http://w3af.com/'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_perc_20(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1%202').url_encode()
        EXPECTED = 'https://w3af.com:443/file.asp?id=1%202'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_space(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1 2').url_encode()
        EXPECTED = 'https://w3af.com:443/file.asp?id=1%202'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_plus(self):
        msg = '''
        When parsing an HTML document that has a link like the one below, can
        the browser (or in this case w3af) know the original intent of the web
        developer?

        Was he trying to put a space or a real "+" ? At the moment of writing
        these lines, w3af thinks that the user is trying to put a "+", so it
        will encode it as a %2B for sending to the wire.
        '''
        raise SkipTest(msg)

        res_str = URL(u'https://w3af.com:443/file.asp?id=1+2').url_encode()
        EXPECTED = 'https://w3af.com:443/file.asp?id=1+2'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_url_encode_plus(self):
        res_str = URL(u'https://w3af.com:443/file.asp?id=1%2B2').url_encode()
        EXPECTED = 'https://w3af.com:443/file.asp?id=1%2B2'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_math(self):
        res_str = URL(u'http://w3af.com/x.py?ec=x*y/2==3').url_encode()
        EXPECTED = 'http://w3af.com/x.py?ec=x%2Ay%2F2%3D%3D3'
        self.assertEqual(res_str, EXPECTED)

    def test_encode_param(self):
        res_str = URL(u'http://w3af.com/x.py;id=1?y=3').url_encode()
        EXPECTED = 'http://w3af.com/x.py;id=1?y=3'
        self.assertEqual(res_str, EXPECTED)

    def test_decode_encode(self):
        '''Encode and Decode should be able to run one on the result of the
        other and return the original'''
        original = URL(u'https://w3af.com:443/file.asp?id=1%202')
        decoded = original.url_decode()
        encoded = decoded.url_encode()
        self.assertEqual(original.url_encode(), encoded)

    def test_encode_decode(self):
        '''Encode and Decode should be able to run one on the result of the
        other and return the original'''
        original = URL(u'https://w3af.com:443/file.asp?id=1%202')
        encoded = original.url_encode()
        decoded = URL(encoded).url_decode()
        self.assertEqual(original, decoded)
