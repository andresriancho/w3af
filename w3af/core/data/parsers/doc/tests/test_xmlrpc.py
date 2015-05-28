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
import unittest
import xml.sax
import cgi

from w3af.core.data.parsers.doc.xmlrpc import XmlRpcReadHandler, XmlRpcWriteHandler


XML_WITH_FUZZABLE = """\
<methodCall>
   <methodName>sample.sum</methodName>
   <params>
       <param>
           <array>
              <data>
                 <value><i4>1404</i4></value>
                 <value><string>Foo bar</string></value>
                 <value><i4>1</i4></value>
                 <value><base64>U3BhbSBlZ2dz</base64></value>
              </data>
           </array>
       </param>
   </params>
</methodCall>"""

XML_WITHOUT_FUZZABLE = """\
<methodCall>
   <methodName>sample.sum</methodName>
   <params>
       <param>
           <array>
               <data>
                   <value><i4>1404</i4></value>
                   <value><i4>1</i4></value>
               </data>
           </array>
       </param>
   </params>
</methodCall>"""


class TestXMLRPC(unittest.TestCase):

    def test_reader(self):
        handler = XmlRpcReadHandler()
        xml.sax.parseString(XML_WITH_FUZZABLE, handler)

        EXPECTED = [(u'string', [u'Foo bar']), (u'base64', [u'Spam eggs'])]

        self.assertEqual(handler.get_data_container().items(), EXPECTED)

    def test_writer(self):
        handler = XmlRpcReadHandler()
        xml.sax.parseString(XML_WITH_FUZZABLE, handler)

        data_container = handler.get_data_container()
        payload = '<script>alert(1)</script>'
        data_container['string'][0] = payload

        handler = XmlRpcWriteHandler(data_container)

        fuzzed = XML_WITH_FUZZABLE.replace('Foo bar', cgi.escape(payload))

        xml.sax.parseString(XML_WITH_FUZZABLE, handler)
        self.assertEqual(handler.fuzzed_xml_string, fuzzed)
