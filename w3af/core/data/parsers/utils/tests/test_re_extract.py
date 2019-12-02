# -*- coding: utf-8 -*-
"""
test_re_extract.py

Copyright 2019 Andres Riancho

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

from w3af.core.data.parsers.utils.re_extract import ReExtract
from w3af.core.data.parsers.doc.url import URL


class TestReExtract(unittest.TestCase):
    def test_relative_regex(self):
        doc_string = '123 ../../foobar/uploads/foo.png 465'
        base_url = URL('https://w3af.org/abc/def/')

        re_extract = ReExtract(doc_string, base_url, 'utf-8')
        re_extract.parse()

        references = re_extract.get_references()

        self.assertEqual(references, [URL('https://w3af.org/foobar/uploads/foo.png')])
