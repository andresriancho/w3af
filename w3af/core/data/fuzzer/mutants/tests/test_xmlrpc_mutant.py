# -*- coding: utf-8 -*-
"""
test_xmlrpc_mutant.py

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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.fuzzer.mutants.xmlrpc_mutant import XmlRpcMutant
from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.tests.test_xmlrpc import (XML_WITH_FUZZABLE)


class TestXMLRPCMutant(unittest.TestCase):

    def get_url(self):
        return URL('http://w3af.com/a/b/c.php')

    def test_from_freq(self):
        freq = FuzzableRequest.from_parts(self.get_url(), 'POST',
                                          XML_WITH_FUZZABLE, Headers())
        m = XmlRpcMutant(freq)

        self.assertIsInstance(m.get_dc(), XmlRpcContainer)

        dc = m.get_dc()
        self.assertIn('string', dc)
        self.assertIn('base64', dc)

        self.assertEqual(len(dc['string']), 1)
        self.assertEqual(len(dc['base64']), 1)

        self.assertEqual(dc['string'][0], 'Foo bar')
        self.assertEqual(dc['base64'][0], 'Spam eggs')

        self.assertEqual(str(m.get_dc()), str(m.get_data()))

        found_at = '"http://w3af.com/a/b/c.php", using HTTP method POST. ' \
                   'The sent XML-RPC was: "<methodCall>\n   <methodName>' \
                   'sample.sum</methodName>\n   <params>\n ".'
        self.assertEqual(m.found_at(), found_at)

        headers = m.get_headers()
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/xml')