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

BOUNDARY = ('boundl', 'boundr')


class TestJavaScriptInHTML(unittest.TestCase):
    def test_payload_script_single_quote(self):
        html = """
        <html>
            <script type="text/javascript">//<!--
                init({login:'',foo:'boundlPAYLOADboundr'})
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertFalse(context.can_break())

    def test_payload_script_single_quote(self):
        html = """
        <html>
            <script type="text/javascript">//<!--
                init({login:'',foo:'boundlPAYLOADboundr'})
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertFalse(context.can_break())

    def test_payload_script_single_quote_can_break(self):
        html = """
        <html>
            <script>
                init({login:'',foo:'boundl'boundr'})
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertTrue(context.can_break())

    def test_payload_script_multi_line_comment(self):
        html = """
        <html>
            <script type="text/javascript">
                /* boundlPAYLOADboundr */
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertFalse(context.can_break())

    def test_payload_script_multi_line_comment_can_break(self):
        html = """
        <html>
            <script>
                /*
                boundl*/boundr
                */
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertTrue(context.can_break())

    def test_payload_script_single_line_comment(self):
        html = """
        <html>
            <script type="text/javascript">
                // boundlPAYLOADboundr
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertFalse(context.can_break())

    def test_payload_script_single_line_comment_can_break_lf(self):
        html = """
        <html>
            <script>
                // boundl\nboundr
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertTrue(context.can_break())

    def test_payload_script_single_line_comment_can_break_ls(self):
        html = """
        <html>
            <script>
                // boundl\xe2\x80\xa8boundr
            </script>
        </html>
        """
        context = get_context(html.decode('utf-8'), BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertTrue(context.can_break())

    def test_payload_script_single_line_html_comment(self):
        html = """
        <html>
            <script type="text/javascript">
                <!-- boundlPAYLOADboundr
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertFalse(context.can_break())

    def test_payload_script_single_line_html_comment_can_break_lf(self):
        html = """
        <html>
            <script>
                <!-- boundl\rboundr
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertTrue(context.can_break())

    def test_payload_script_can_break_html(self):
        html = """
        <html>
            <script>
                'foo: boundl</script>boundr'
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertTrue(context.can_break())

    def test_payload_script_can_break_html_fp(self):
        html = """
        <html>
            <script>
                'foo: boundl<boundr'
            </script>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, ScriptText)
        self.assertFalse(context.can_break())

    def test_payload_javascript_value(self):
        """
        Test for false positive reported at
        https://github.com/andresriancho/w3af/issues/13359

        :return: Should not find a XSS
        """
        html = """
        <html>
            <form>
                <input type="text" name="test" value="boundl:boundr">
                <input type="submit">
            </form>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.is_executable())
        self.assertFalse(context.can_break())

    def test_payload_javascript_href(self):
        html = """
        <html>
            <a href="javascript:boundlPAYLOADboundr">foo</a>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())

    def test_payload_javascript_href_append(self):
        html = """
        <html>
            <a href="javascript:foo();boundlPAYLOADboundr">foo</a>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())

    def test_payload_javascript_href_start_with_space(self):
        html = """
        <html>
            <a href=" javascript:foo();boundlPAYLOADboundr">foo</a>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())

    def test_payload_href_append_no_exec(self):
        html = """
        <html>
            <a href="http://w3af.org/boundlPAYLOADboundr">foo</a>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.is_executable())

    def test_payload_js_doublequote(self):
        html = """
        <html>
            <input type="button" value="ClickMe" onClick="boundlPAYLOADboundr">
        </html>
        """
        contexts = get_context(html, BOUNDARY)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())
        self.assertFalse(context.can_break())

    def test_payload_onclick_payload_between_single_quotes(self):
        html = """
        <html>
            <input type="button" onClick="foo('boundl'boundr')">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)

        self.assertTrue(context.can_break())

    def test_payload_onclick_payload_between_single_quotes_append(self):
        html = """
        <html>
            <input type="button" onClick="foo('XXX-boundl'boundr')">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)

        self.assertTrue(context.can_break())

    def test_payload_onclick_htmlencoded_payload_between_single_quotes(self):
        html = """
        <html>
            <input type="button" onClick="
                foo(&apos;boundl&#39;boundr&#x27;)
            ">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.can_break())

    def test_payload_onclick_htmlencoded_payload_escaped_payload_fp(self):
        html = """
        <html>
            <input type="button" onClick="
                foo(&apos;boundl&amp;#39;boundr&#x27;)
            ">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.can_break())
        self.assertFalse(context.is_executable())

    def test_payload_onclick_htmlencoded_payload_escaped_literal_fp(self):
        html = """
        <html>
            <input type="button" onClick="
                foo('&amp;#39;boundlPAYLOADboundr&amp;#39;')
            ">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.can_break())
        self.assertFalse(context.is_executable())

    def test_payload_onclick_payload_append(self):
        html = """
        <html>
            <input type="button" onClick="XXX - boundlPAYLOADboundr">
        </html>
        """

        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertFalse(context.can_break())
        self.assertTrue(context.is_executable())

    def test_payload_onclick_payload_between_double_quotes(self):
        html = """
        <html>
            <input type="button" onClick='foo("boundl"boundr")'>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, HtmlAttrSingleQuote)
        self.assertTrue(context.can_break())

    def test_payload_onclick_payload_htmlencoded_between_double_quotes(self):
        html = """
        <html>
            <input type="button" onClick='foo("boundl&quot;boundr")'>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, HtmlAttrSingleQuote)
        self.assertTrue(context.can_break())

    def test_payload_onclick_payload_comment_between_double_quotes(self):
        html = """
        <html>
            <input type="button" onClick='foo("foo", /*"boundl*/boundr"*/)'>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, HtmlAttrSingleQuote)
        self.assertTrue(context.can_break())

    def test_payload_onclick_payload_no_quotes(self):
        """
        In this case I'm already running code, if I would send alert(1) as
        payload it would be run, so no need to escape from any string delimiter
        such as " or '
        """
        html = """
        <html>
            <input type="button" onClick="foo(boundlPAYLOADboundr)">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrDoubleQuote)
        self.assertTrue(context.is_executable())
        self.assertFalse(context.can_break())

    def test_payload_onclick_payload_separated_with_semicolon(self):
        html = """
        <html>
            <input type="button" onclick="foo();boundlPAYLOADboundr;bar()">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

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
                   src='javascript:var name="boundl"boundr"; alert(name);'>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]

        self.assertIsInstance(context, HtmlAttrSingleQuote)
        self.assertTrue(context.can_break())

    def test_payload_src(self):
        html = """
        <html>
            <img src="boundljavascript:boundr" />
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertTrue(context.can_break())
        self.assertIsInstance(context, HtmlAttrDoubleQuote)

    def test_payload_handler(self):
        html = """
        <html>
            <a onclick="boundlPAYLOADboundr">foo</a>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertTrue(context.is_executable())
        self.assertIsInstance(context, HtmlAttrDoubleQuote)

    def test_payload_href(self):
        html = """
        <html>
            <a href="boundljavascript:boundr">foo</a>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertTrue(context.can_break())
        self.assertIsInstance(context, HtmlAttrDoubleQuote)

    def test_payload_href_escaped(self):
        html = """
        <html>
            <a href="boundljavascript&colon;boundr">foo</a>
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertTrue(context.can_break())
        self.assertIsInstance(context, HtmlAttrDoubleQuote)

    def test_payload_html_inside_script_with_comment(self):
        html = """
        <html>
            <script>
                <!-- foo();boundlPAYLOADboundr;bar(); -->
            </script>
        </html>
        """
        self.assertIsInstance(get_context(html, BOUNDARY)[0], ScriptText)

    def test_payload_with_space_equal_not_executable_attr(self):
        """
        Related with:
            https://github.com/andresriancho/w3af/issues/1557
            https://github.com/andresriancho/w3af/issues/2919
        """
        html = """
        <html>
            <frame bar="boundlPAYLOADboundr">
        </html>
        """
        context = get_context(html, BOUNDARY)[0]
        self.assertFalse(context.is_executable())
