"""
test_xml_bones.py

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

from w3af.core.data.misc.xml_bones import get_xml_bones


class TestXMLBones(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(get_xml_bones(''), '')

    def test_simple(self):
        self.assertEqual(get_xml_bones('<xml>hello</xml>'),
                        'html\nbody\nxml\n0\nxml\nbody\nhtml')

    def test_large(self):
        self.assertEqual(get_xml_bones('<xml>hello world 123 123</xml>'),
                         'html\nbody\nxml\n20\nxml\nbody\nhtml')

    def test_extra_large_1(self):
        self.assertEqual(get_xml_bones('<xml>%s</xml>' % ('A' * 30,)),
                         'html\nbody\nxml\n40\nxml\nbody\nhtml')

    def test_extra_large_2(self):
        # Just adding one more char to the end
        self.assertEqual(get_xml_bones('<xml>%s</xml>' % ('A' * 41,)),
                         'html\nbody\nxml\n40\nxml\nbody\nhtml')

    def test_attr(self):
        self.assertEqual(get_xml_bones('<xml id=1>hello</xml>'),
                         'html\nbody\nxml\nid0\n0\nxml\nbody\nhtml')

    def test_broken_1(self):
        self.assertEqual(get_xml_bones('<xml '),
                         'html\nbody\nxml\nbody\nhtml')

    def test_broken_2(self):
        self.assertEqual(get_xml_bones('<xml>'),
                         'html\nbody\nxml\nxml\nbody\nhtml')

    def test_nested(self):
        self.assertEqual(get_xml_bones('<a><b>hello</b></a>'),
                         'html\nbody\na\nb\n0\nb\na\nbody\nhtml')

    def test_just_text(self):
        self.assertEqual(get_xml_bones('hello world (); foobar'),
                         'html\nbody\np\n20\np\nbody\nhtml')
