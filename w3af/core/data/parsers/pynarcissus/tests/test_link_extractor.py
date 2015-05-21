"""
test_link_extractor.py

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

from w3af.core.data.parsers import URL_RE
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.pynarcissus.link_extractor import JSLinkExtractor
from w3af.core.data.parsers.pynarcissus.tests.test_string_extractor import JSParserMixin


class TestLinkExtractor(unittest.TestCase, JSParserMixin):
    """
    :see: Docstring in StringExtractor
    """
    def test_jquery(self):
        e = JSLinkExtractor(self.get_file_contents('jquery.js'))
        expected = set()

        self.assertEqual(e.get_links(), expected)

    def test_jquery_re(self):
        urls = set()
        merged_strings = self.get_file_contents('jquery.js')

        for x in URL_RE.findall(merged_strings):
            try:
                urls.add(URL(x[0]))
            except ValueError:
                pass

        return urls