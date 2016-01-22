"""
test_javascript_in_html.py

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
from w3af.core.data.context.context.html import (ScriptText,
                                                 HtmlAttrSingleQuote,
                                                 HtmlAttrDoubleQuote)


class TestJavaScriptInHTML(unittest.TestCase):
    def test_payload_script_single_quote(self):
        html = """
        <html>
            <script type="text/javascript">//<!--
                init({login:'',foo:'PAYLOAD'})
            </script>
        </html>
        """
        payload = 'PAYLOAD'
        context = get_context(html, payload)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertFalse(context.can_break())

    def test_payload_script_single_quote_can_break(self):
        html = """
        <html>
            <script>
                init({login:'',foo:'PAYLOAD'BREAK'})
            </script>
        </html>
        """
        payload = "PAYLOAD'BREAK"
        context = get_context(html, payload)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertTrue(context.can_break())

    def test_payload_javascript_value(self):
        """
        Test for false positive reported at
        https://github.com/andresriancho/w3af/issues/13359

        :return: Should not find a XSS
        """
        payload = 'PAYLOAD:PAYLOAD'
        html = """
        <html>
            <form>
                <input type="text" name="test" value="%s">
                <input type="submit">
            </form>
        </html>
        """
        context = get_context(html % payload, payload)[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.is_executable())
        self.assertFalse(context.can_break())

    def test_payload_javascript_href(self):
        html = """
        <html>
            <a href="javascript:PAYLOAD">foo</a>
        </html>
        """
        context = get_context(html, 'PAYLOAD')[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())

    def test_payload_javascript_href_append(self):
        html = """
        <html>
            <a href="javascript:foo();PAYLOAD">foo</a>
        </html>
        """
        context = get_context(html, 'PAYLOAD')[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())

    def test_payload_javascript_href_start_with_space(self):
        html = """
        <html>
            <a href=" javascript:foo();PAYLOAD">foo</a>
        </html>
        """
        context = get_context(html, 'PAYLOAD')[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())

    def test_payload_href_append_no_exec(self):
        html = """
        <html>
            <a href="http://w3af.org/PAYLOAD">foo</a>
        </html>
        """
        context = get_context(html, 'PAYLOAD')[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.is_executable())

    def test_payload_js_doublequote(self):
        html = """
        <html>
            <input type="button" value="ClickMe" onClick="PAYLOAD">
        </html>
        """
        payload = 'PAYLOAD'
        contexts = get_context(html, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())
        self.assertFalse(context.can_break())

    def test_payload_onclick_payload_between_single_quotes(self):
        html = """
        <html>
            <input type="button" onClick="foo('PAYLOAD'BREAK')">
        </html>
        """
        payload = "PAYLOAD'BREAK"
        context = get_context(html, payload)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)

        self.assertTrue(context.can_break())

    def test_payload_onclick_payload_between_single_quotes_append(self):
        html = """
        <html>
            <input type="button" onClick="foo('XXX-PAYLOAD'BREAK')">
        </html>
        """
        payload = "PAYLOAD'BREAK"
        context = get_context(html, payload)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)

        self.assertTrue(context.can_break())

    def test_payload_onclick_payload_append(self):
        html = """
        <html>
            <input type="button" onClick="XXX - PAYLOAD">
        </html>
        """
        payload = "PAYLOAD"
        context = get_context(html, payload)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.can_break())
        self.assertTrue(context.is_executable())

    def test_payload_onclick_payload_between_double_quotes(self):
        html = """
        <html>
            <input type="button" onClick="foo('PAYLOAD'BREAK')">
        </html>
        """
        payload = "PAYLOAD'BREAK"

        contexts = get_context(html, payload)
        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.can_break())

    def test_payload_onclick_payload_no_quotes(self):
        """
        In this case I'm already running code, if I would send alert(1) as
        payload it would be run, so no need to escape from any string delimiter
        such as " or '
        """
        html = """
        <html>
            <input type="button" onClick="foo(PAYLOAD)">
        </html>
        """
        payload = 'PAYLOAD'
        context = get_context(html, payload)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())
        self.assertFalse(context.can_break())

    def test_payload_onclick_payload_separated_with_semicolon(self):
        html = """
        <html>
            <input type="button" onclick="foo();PAYLOAD;bar()">
        </html>
        """
        payload = 'PAYLOAD'
        context = get_context(html, payload)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())
        self.assertFalse(context.can_break())

    def test_payload_wavsep_case17_frame_src(self):
        """
        :see: http://127.0.0.1:8098/active/Reflected-XSS/
                                   /RXSS-Detection-Evaluation-GET/
                                   Case17-Js2PropertyJsScopeDoubleQuoteDelimiter
                                   .jsp?userinput=dav%22id
        """
        html = """
        <html>
            <frame name='frame2' id='frame2'
                   src='javascript:var name="PAYLOAD"BREAK"; alert(name);'>
        </html>
        """
        payload = 'PAYLOAD"BREAK'
        context = get_context(html, payload)[0]

        self.assertIsInstance(context, HtmlAttrSingleQuote)
        self.assertTrue(context.can_break())

    def test_payload_src(self):
        html = """
        <html>
            <img src="%s" />
        </html>
        """
        payload = 'PAYLOAD:'
        context = get_context(html % payload, payload)[0]
        self.assertTrue(context.can_break())
        self.assertIsInstance(context, HtmlAttrDoubleQuote)

    def test_payload_handler(self):
        html = """
        <html>
            <a onclick="PAYLOAD">foo</a>
        </html>
        """
        context = get_context(html, 'PAYLOAD')[0]
        self.assertTrue(context.is_executable())
        self.assertIsInstance(context, HtmlAttrDoubleQuote)

    def test_payload_href(self):
        payload = 'PAYLOAD:'
        html = """
        <html>
            <a href="%s">foo</a>
        </html>
        """
        context = get_context(html % payload, payload)[0]
        self.assertTrue(context.can_break())
        self.assertIsInstance(context, HtmlAttrDoubleQuote)

    def test_payload_html_inside_script_with_comment(self):
        html = """
        <html>
            <script>
                <!-- foo();PAYLOAD;bar(); -->
            </script>
        </html>
        """
        self.assertIsInstance(get_context(html, 'PAYLOAD')[0], ScriptText)

    def test_payload_with_space_equal_not_executable_attr(self):
        """
        Related with:
            https://github.com/andresriancho/w3af/issues/1557
            https://github.com/andresriancho/w3af/issues/2919
        """
        html = """
        <html>
            <frame bar="PAYLOAD">
        </html>
        """
        context = get_context(html, 'PAYLOAD')[0]
        self.assertFalse(context.is_executable())

    def test_payload_with_space_equal_src_executable(self):
        """
        Related with:
            https://github.com/andresriancho/w3af/issues/1557
            https://github.com/andresriancho/w3af/issues/2919
        """
        html = """
        <html>
            <frame src="5vrws =">
        </html>
        """
        self.assertEqual(get_context(html, '5vrws%20%3D'), [])
