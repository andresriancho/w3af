"""
test_headers_mutant.py

Copyright 2006 Andres Riancho

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
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.dc.headers import Headers


class TestHeadersMutant(unittest.TestCase):

    def setUp(self):
        self.payloads = ['abc', 'def']
        self.fuzzer_config = {'fuzzable_headers': ['Referer']}

    def test_basic(self):
        referer_1 = 'http://w3af.org/'
        referer_2 = 'http://spam.w3af.org/'

        freq = FuzzableRequest(URL('http://www.w3af.com/'),
                               headers=Headers([('Referer', referer_1)]))
        self.assertEqual(freq.get_referer(), referer_1)

        m = HeadersMutant(freq)
        m.get_dc().set_token(('Referer',))
        m.set_token_value(referer_2)

        self.assertEqual(m.get_token_value(), referer_2)

    def test_found_at(self):
        headers = Headers([('Referer', 'http://moth/')])
        freq = FuzzableRequest(URL('http://www.w3af.com/?id=3'),
                               headers=headers)
        m = HeadersMutant(freq)
        m.get_dc().set_token(('Referer',))
        m.set_token_value('foo')

        expected = '"http://www.w3af.com/", using HTTP method GET. The'\
                   ' modified header was: "Referer" and it\'s value was: "foo".'
        self.assertEqual(m.found_at(), expected)

    def test_mutant_creation(self):
        url = URL('http://moth/?a=1&b=2')
        original_referer = 'http://moths/'
        headers = Headers([('Referer', original_referer)])
        freq = FuzzableRequest(url, headers=headers)

        created_mutants = HeadersMutant.create_mutants(freq, self.payloads, [],
                                                       False,
                                                       self.fuzzer_config)

        expected_strs = {'Referer: abc\r\n',
                         'Referer: def\r\n'}
        expected_dcs = [Headers([('Referer', 'abc')]),
                        Headers([('Referer', 'def')])]

        created_dcs = [i.get_dc() for i in created_mutants]
        created_strs = set([str(i.get_dc()) for i in created_mutants])

        self.assertEqual(created_dcs, expected_dcs)
        self.assertEqual(created_strs, expected_strs)

        token = created_mutants[0].get_token()
        self.assertEqual(token.get_name(), 'Referer')
        self.assertEqual(token.get_original_value(), original_referer)
        self.assertEqual(token.get_value(), 'abc')

        token = created_mutants[1].get_token()
        self.assertEqual(token.get_name(), 'Referer')
        self.assertEqual(token.get_original_value(), original_referer)
        self.assertEqual(token.get_value(), 'def')

        for m in created_mutants:
            self.assertIsInstance(m, HeadersMutant)
