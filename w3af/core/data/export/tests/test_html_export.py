"""
test_html_export.py

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

from w3af.core.data.export.html_export import html_export

EXPECTED_SIMPLE = """
<form action="http://www.w3af.org/" method="GET">
<input type="submit">
</form>
"""

EXPECTED_POST = """
<form action="http://www.w3af.org/" method="POST">
<label>a</label>
<input type="text" name="a" value="1">
<input type="submit">
</form>
"""

EXPECTED_POST_REPEATED = """
<form action="http://www.w3af.org/" method="POST">
<label>a</label>
<input type="text" name="a" value="1">
<label>a</label>
<input type="text" name="a" value="2">
<input type="submit">
</form>
"""


class TestHTMLExport(unittest.TestCase):

    def test_export_GET(self):
        http_request = 'GET http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Foo: bar\n' \
                       '\n'
        html_code = html_export(http_request)
        self.assertTrue(EXPECTED_SIMPLE in html_code)

    def test_export_POST(self):
        http_request = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 3\n' \
                       'Content-Type: application/x-www-form-urlencoded\n' \
                       '\n' \
                       'a=1'
        html_code = html_export(http_request)
        self.assertTrue(EXPECTED_POST in html_code)

    def test_export_POST_repeated(self):
        http_request = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 7\n' \
                       'Content-Type: application/x-www-form-urlencoded\n' \
                       'Foo: spam\n' \
                       'Foo: eggs\n' \
                       '\n' \
                       'a=1&a=2'
        html_code = html_export(http_request)
        self.assertTrue(EXPECTED_POST_REPEATED in html_code)

    def test_export_inject(self):
        http_request = 'POST http://www.w3af.org/ HTTP/1.1\n' \
                       'Host: www.w3af.org\n' \
                       'Content-Length: 7\n' \
                       'Content-Type: application/x-www-form-urlencoded\n' \
                       'Foo: spam\n' \
                       'Foo: eggs\n' \
                       '\n' \
                       'a"<=1&a=2"<3'
        html_code = html_export(http_request)
        self.assertTrue('"2&quot;&lt;3"' in html_code)
        self.assertTrue('"a&quot;&lt;"' in html_code)
