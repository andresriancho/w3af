"""
test_css_style.py

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

class TestHTMLContext(unittest.TestCase):

    SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'samples')

    def test_style_comment_case01(self):
        style_comment = """
        <html>
            <head>
                <style>
                /*
                Hello STYLE_COMMENT world
                 * */
                </style>
            </head>
        </html>
        """
        self.assertEqual(
                get_context(style_comment, StyleComment().get_name())[1].get_name(),
                StyleComment().get_name()
               )

    def test_style_comment_case02(self):
        style_comment = """
        <html>
            <head>
                <style>
                /*
                Hello world
                 * */
                </style>
                <style>
                    PAYLOAD
                </style>
            </head>
        </html>
        """

        self.assertEqual(
                         get_context(style_comment, 'PAYLOAD')[0].get_name(),
                         StyleText().get_name()
               )