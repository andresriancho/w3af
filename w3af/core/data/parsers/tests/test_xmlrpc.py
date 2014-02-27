"""
test_xmlrpc.py

Copyright 2012 Andres Riancho

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
import copy
import unittest
import xml.sax

from w3af.core.data.parsers.xmlrpc import xmlrpc_read_handler, xmlrpc_write_handler


class TestXMLRPC(unittest.TestCase):

    def test_reader(self):
        handler = xmlrpc_read_handler()

        s = """
         <array>
           <data>
             <value><i4>1404</i4></value>
             <value><string>Foo bar</string></value>
             <value><i4>1</i4></value>
             <value><string>Spam eggs</string></value>
           </data>
         </array>"""

        xml.sax.parseString(s, handler)

        EXPECTED = [[u'string', u'Foo bar'], [u'string', u'Spam eggs']]

        self.assertEqual(handler.fuzzable_parameters, EXPECTED)

    def test_writer(self):
        fuzzable_parameters = [[u'string', u'Foo bar'], [u'string',
                                                         u'Spam eggs']]
        fuzzable_parameters = copy.deepcopy(fuzzable_parameters)
        fuzzable_parameters[0][1] = '<script>alert(1)</script>'

        handler = xmlrpc_write_handler(fuzzable_parameters)

        original = """<array>
           <data>
             <value a="ab"><i4>1404</i4></value>
             <value><string>Foo bar</string></value>
             <value><i4>1</i4></value>
             <value><string>Spam eggs</string></value>
           </data>
         </array>"""

        fuzzed = """<array>
           <data>
             <value a="ab"><i4>1404</i4></value>
             <value><string>&lt;script&gt;alert(1)&lt;/script&gt;</string></value>
             <value><i4>1</i4></value>
             <value><string>Spam eggs</string></value>
           </data>
         </array>"""

        xml.sax.parseString(original, handler)
        self.assertEqual(handler.fuzzed_xml_string, fuzzed)
