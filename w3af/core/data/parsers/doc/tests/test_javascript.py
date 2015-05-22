# -*- coding: UTF-8 -*-
"""
test_javascript.py

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
import os

from w3af.core.data.parsers.doc.javascript import JavaScriptParser
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.url import URL


class TestJavaScriptParser(unittest.TestCase):

    DATA_PATH = 'w3af/core/data/parsers/pynarcissus/tests/data/'

    def parse(self, filename):
        body = file(os.path.join(self.DATA_PATH, filename)).read()
        js_mime = 'text/javascript'
        hdrs = Headers({'Content-Type': js_mime}.items())
        response = HTTPResponse(200, body, hdrs,
                                URL('http://moth/xyz/'),
                                URL('http://moth/xyz/'),
                                _id=1)

        parser = JavaScriptParser(response)
        parser.parse()
        return parser

    def test_false_positives(self):
        for filename in ('jquery.js', 'angular.js', 'test_1.js', 'test_2.js',
                         'test_3.js'):
            p = self.parse(filename)
            self.assertEqual(p.get_references(), ([], []))

    def test_relative(self):
        p = self.parse('test_4.js')
        expected = [], [URL('http://moth/spam.html'),
                        URL('http://moth/eggs.html')]
        self.assertEqual(p.get_references(), expected)

    def test_full(self):
        p = self.parse('test_full_url.js')
        expected = [], [URL('http://moth/spam.html'),
                        URL('http://moth/eggs.html')]
        self.assertEqual(p.get_references(), expected)