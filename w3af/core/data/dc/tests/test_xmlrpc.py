"""
test_xmlrpc.py

Copyright 2014 Andres Riancho

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
import copy

from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.parsers.doc.tests.test_xmlrpc import (XML_WITH_FUZZABLE,
                                                      XML_WITHOUT_FUZZABLE)


class TestXMLRPC(unittest.TestCase):

    def test_with_fuzzable_params(self):
        dc = XmlRpcContainer(XML_WITH_FUZZABLE)

        self.assertIn('string', dc)
        self.assertIn('base64', dc)

        self.assertEqual(len(dc['string']), 1)
        self.assertEqual(len(dc['base64']), 1)

        self.assertEqual(dc['string'][0], 'Foo bar')
        self.assertEqual(dc['base64'][0], 'Spam eggs')

        self.assertEqual(str(dc), XML_WITH_FUZZABLE)

    def test_copy(self):
        dc = XmlRpcContainer(XML_WITH_FUZZABLE)
        self.assertEqual(dc, copy.deepcopy(dc))

    def test_without_fuzzable_params(self):
        dc = XmlRpcContainer(XML_WITHOUT_FUZZABLE)

        self.assertEqual(len(dc), 0)
        self.assertEqual(str(dc), XML_WITHOUT_FUZZABLE)

    def test_simple_fuzzing(self):
        dc = XmlRpcContainer(XML_WITH_FUZZABLE)

        dc.set_token(('string', 0))
        token = dc.get_token()

        self.assertEqual(token.get_value(), 'Foo bar')

        token.set_value('bacon')
        expected = XML_WITH_FUZZABLE.replace('Foo bar', 'bacon')

        self.assertEqual(str(dc), expected)
