"""
test_html_css.py

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
import unittest

from w3af.core.data.context.context.main import get_context
from w3af.core.data.context.context.html import (CSSText,
                                                 HtmlAttrSingleQuote,
                                                 HtmlAttrDoubleQuote)


class TestStyleInHTML(unittest.TestCase):
    def test_payload_style_single_quote_break(self):
        html = """
        <html>
            <style>
                font-family: Georgia, "Times New Roman %s";
            </style>
        </html>
        """
        payload = 'PAYLOAD":('
        context = get_context(html % payload, payload)[0]
        self.assertIsInstance(context, CSSText)
        self.assertTrue(context.can_break())

    def test_payload_style_single_quote_no_break(self):
        html = """
        <html>
            <style>
                font-family: Georgia, "Times New Roman %s";
            </style>
        </html>
        """
        payload = 'PAYLOAD":('
        escaped_payload = payload.replace('"', '\\"')
        contexts = get_context(html % escaped_payload, payload)
        self.assertEqual(len(contexts), 0)

    def test_payload_inline_single(self):
        html = """
        <div style='background-image: url("%s")'>
        """
        payload = 'PAYLOAD":('
        context = get_context(html % payload, payload)[0]
        self.assertIsInstance(context, HtmlAttrSingleQuote)
        self.assertTrue(context.can_break())

    def test_payload_inline_single_no_break(self):
        html = """
        <div style='background-image: url("%s")'>
        """
        payload = 'PAYLOAD":('
        escaped_payload = payload.replace('"', '')
        contexts = get_context(html % escaped_payload, payload)
        self.assertEqual(len(contexts), 0)

    def test_payload_inline_double(self):
        html = """
        <div style="background-image: url('%s')">
        """
        payload = "PAYLOAD':("
        context = get_context(html % payload, payload)[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.can_break())

    def test_style_comment_1(self):
        html = """
        <html>
            <head>
                <style>
                /*
                Hello %s world
                 * */
                </style>
            </head>
        </html>
        """
        payload = 'PAYLOAD*/:('
        context = get_context(html % payload, payload)[0]
        self.assertIsInstance(context, CSSText)
        self.assertTrue(context.can_break())

    def test_style_comment_2(self):
        html = """
        <html>
            <head>
                <style>
                /*
                Hello world
                 * */
                </style>

                <style>
                    %s
                </style>
            </head>
        </html>
        """
        payload = 'PAYLOAD:('
        context = get_context(html % payload, payload)[0]
        self.assertIsInstance(context, CSSText)
        self.assertTrue(context.can_break())
