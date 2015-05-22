"""
test_wml_parser.py

Copyright 2006 Andres Riancho

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

from w3af.core.data.parsers.doc.wml_parser import WMLParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse as HTTPResponse
from w3af.core.data.dc.headers import Headers


class TestWMLParser(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://www.w3af.com/')

    def test_parser_simple_form(self):
        form = """<go method="post" href="post.php">
                    <postfield name="clave" value="$(clave)"/>
                    <postfield name="cuenta" value="$(cuenta)"/>
                    <postfield name="tipdat" value="D"/>
                </go>"""
        
        response = HTTPResponse(200, form, Headers(), self.url, self.url)
        
        w = WMLParser(response)
        w.parse()
        forms = w.get_forms()
        
        self.assertEqual(len(forms), 1)
        form = forms[0]
        
        self.assertEqual(form.get_action().url_string,
                         u'http://www.w3af.com/post.php')
        
        self.assertIn('clave', form)
        self.assertIn('cuenta', form)
        self.assertIn('tipdat', form)

    def test_parser_simple_link(self):
        response = HTTPResponse(200, '<a href="/index.aspx">ASP.NET</a>',
                                Headers(), self.url, self.url)
        w = WMLParser(response)
        w.parse()
        re, parsed = w.get_references()
        
        # TODO: Shouldn't this be the other way around?!
        self.assertEqual(len(parsed), 0)
        self.assertEqual(u'http://www.w3af.com/index.aspx', re[0].url_string)

