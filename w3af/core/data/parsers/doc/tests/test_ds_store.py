# -*- coding: UTF-8 -*-
"""
test_ds_store.py

Copyright 2015 Andres Riancho

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
from w3af.core.data.parsers.doc.ds_store_parser import DSStoreParser
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL


class TestDSStore(unittest.TestCase):

    SAMPLE_FMT = 'DS_Store-%s'
    SAMPLE_DIR = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc',
                              'tests', 'data')

    def test_parse_empty(self):
        self.assertRaises(AssertionError, self.parse_body, '')

    def test_parse_invalid_dsstore(self):
        self.assertRaises(AssertionError, self.parse_body, 'AAAAAA')

    def test_parse_invalid_dsstore_2(self):
        self.assertRaises(AssertionError, self.parse_body, '<html>..!')

    def test_parse_sample_0(self):
        parser = self.parse_ds_store(0)
        extracted, _ = parser.get_references()

        expected = {
            URL('http://moth/objects'),
            URL('http://moth/current'),
            URL('http://moth/page break.jpg'),
            URL('http://moth/publications'),
            URL('http://moth/AHheader.jpg'),
            URL('http://moth/projects'),
            URL('http://moth/scripts'),
            URL('http://moth/email.jpg'),
            URL('http://moth/15x15shim.jpg'),
            URL('http://moth/selectedpress'),
            }

        self.assertEqual(extracted, expected)

    def test_parse_sample_1(self):
        parser = self.parse_ds_store(1)
        extracted, _ = parser.get_references()

        self.assertEqual(extracted, {URL('http://moth/targets'),
                                     URL('http://moth/isiah-jones')})

    def test_parse_sample_2(self):
        parser = self.parse_ds_store(2)
        extracted, _ = parser.get_references()

        self.assertEqual(extracted, {URL('http://moth/priv')})

    def test_parse_sample_3(self):
        parser = self.parse_ds_store(3)
        extracted, _ = parser.get_references()

        self.assertEqual(extracted, {URL('http://moth/javascript'),
                                     URL('http://moth/images'),
                                     URL('http://moth/css'),
                                     URL('http://moth/includes'),
                                     URL('http://moth/pages'),
                                     URL('http://moth/headers')})

    def parse_ds_store(self, sample_id):
        filename = os.path.join(self.SAMPLE_DIR, self.SAMPLE_FMT % sample_id)
        body = file(filename).read()
        return self.parse_body(body)

    def parse_body(self, body):
        hdrs = Headers({'Content-Type': 'text/plain'}.items())
        response = HTTPResponse(200, body, hdrs,
                                URL('http://moth/'),
                                URL('http://moth/'),
                                _id=1)

        assert DSStoreParser.can_parse(response)

        parser = DSStoreParser(response)
        parser.parse()

        return parser