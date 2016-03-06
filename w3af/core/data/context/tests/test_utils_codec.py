"""
test_utils_codec.py

Copyright 2016 Andres Riancho

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
import w3af.core.data.context.utils as context_utils
from w3af.core.data.context.constants import CONTEXT_DETECTOR

BOUNDARY = ('bl', 'br')


class TestUtilsCodec(unittest.TestCase):
    def _count_contexts(self, body):
        return body.count(CONTEXT_DETECTOR) / 2

    def test_encode_empty(self):
        body = ''
        body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(body), 0)

    def test_encode_wo_boundary(self):
        body = 'foobar'
        body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(body), 0)

    def test_encode_simple(self):
        body = 'fooblbarbr'
        body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(body), 1)

    def test_encode_multiply(self):
        body = '''
        foo
        blONEbr
        blTWObr
        '''
        body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(body), 2)

    def test_encode_multiply_broken_left(self):
        body = '''
        foo
        blblblbl
        blONEbr
        blTWObr
        '''
        body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(body), 2)

    def test_encode_multiply_broken_right(self):
        body = '''
        foo
        blONEbr
        blTWObr
        brbrbrbr
        bar
        '''
        body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(body), 2)

    def test_encode_multiply_broken_both(self):
        body = '''
        foo
        blblblbl
        blONEbr
        blTWObr
        brbrbrbr
        bar
        '''
        body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(body), 2)

    def test_decode_simple(self):
        body = '''
        foo
        blONEbr
        bar
        '''
        encoded_body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(encoded_body), 1)
        payloads, content = context_utils.decode_payloads(encoded_body)
        self.assertEqual(content, body)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads.pop(), 'blONEbr')

    def test_decode_multiply(self):
        body = '''
        foo
        {}{}
        bar
        '''
        payloads = {'blONEbr', 'blTWObr'}
        body = body.format(*payloads)
        encoded_body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(encoded_body), 2)
        decoded_payloads, content = context_utils.decode_payloads(encoded_body)
        self.assertEqual(content, body)
        self.assertEqual(len(decoded_payloads), 2)
        self.assertEqual(set(decoded_payloads), set(payloads))

    def test_decode_similar(self):
        body = '''
        foo
        {}{}{}{}{}
        bar
        '''
        payloads = ['blONEbr', 'blONEbr', 'blTWObr', 'blTWObr', 'blTHREEbr']
        body = body.format(*payloads)
        encoded_body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(encoded_body), 5)
        decoded_payloads, content = context_utils.decode_payloads(encoded_body)
        self.assertEqual(content, body)
        self.assertEqual(len(decoded_payloads), 3)
        self.assertEqual(set(decoded_payloads), set(payloads))

    def test_encode_decode_unicode(self):
        body = '''
        foo
        %s
        bar
        '''
        payload = u'bl\r\u2028\u2029\nbr'
        body %= payload
        encoded_body = context_utils.encode_payloads(BOUNDARY, body)
        self.assertEqual(self._count_contexts(encoded_body), 1)
        decoded_payloads, content = context_utils.decode_payloads(encoded_body)
        self.assertEqual(content, body)
        self.assertEqual(len(decoded_payloads), 1)
        self.assertEqual(decoded_payloads.pop(), payload)
