"""
test_multi_json_doc.py

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

from w3af.core.controllers.chrome.utils.multi_json_doc import parse_multi_json_docs


class TestMultipleJSONDocParser(unittest.TestCase):
    def test_one_doc(self):
        one_doc = '{"method":"Page.frameStoppedLoading","params":{"frameId":"..."}}'

        count = 0

        for message in parse_multi_json_docs(one_doc):
            count += 1
            self.assertIsInstance(message, dict)

        self.assertEqual(count, 1)

    def test_two_docs(self):
        two_docs = ('{"method":"Page.frameStoppedLoading","params":{"frameId":"..."}}'
                    '{"method":"Page.frameStoppedLoading","params":{"frameId":"..."}}')

        count = 0

        for message in parse_multi_json_docs(two_docs):
            count += 1
            self.assertIsInstance(message, dict)

        self.assertEqual(count, 2)

    def test_three_docs(self):
        three_docs = ('{"method":"Page.frameStoppedLoading","params":{"frameId":"..."}}'
                      '{"method":"Page.frameStoppedLoading","params":{"frameId":"..."}}'
                      '{"method":"Page.frameStoppedLoading","params":{"frameId":"..."}}')

        count = 0

        for message in parse_multi_json_docs(three_docs):
            count += 1
            self.assertIsInstance(message, dict)

        self.assertEqual(count, 3)
