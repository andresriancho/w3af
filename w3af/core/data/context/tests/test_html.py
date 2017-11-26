"""
test_html_contexts.py

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
import os

from w3af.core.data.context.utils import place_boundary
from w3af.core.data.context.tests.context_test import ContextTest
from w3af.core.data.context.context import get_context
from w3af.core.data.context.context.html import (HtmlTag,
                                                 CSSText,
                                                 HtmlAttr,
                                                 HtmlRawText,
                                                 HtmlText,
                                                 ScriptText,
                                                 HtmlComment,
                                                 HtmlTagClose,
                                                 HtmlAttrNoQuote,
                                                 HtmlAttrBackticks,
                                                 HtmlAttrSingleQuote,
                                                 HtmlAttrDoubleQuote)

BOUNDARY = ('boundl', 'boundr')


class TestHTMLContext(ContextTest):

    SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'samples')

    def test_payload_only_payload(self):
        html = 'boundlPAYLOADboundr'
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlText)

    def test_payload_empty(self):
        html = ''
        self.assertEqual(get_context(html, BOUNDARY), [])

    def test_payload_in_html_text(self):
        html = """
        <html>
            <body>
                boundlPAYLOADboundr
            </body>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlText)

    def test_payload_in_html_raw_text_textarea(self):
        html = """
        <html>
            <textarea>
                boundlPAYLOADboundr
            </textarea>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlRawText)

    def test_payload_in_html_raw_text_title(self):
        html = """
        <html>
            <title>boundlPAYLOADboundr</title>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlRawText)

    def test_payload_in_html_text_with_lower(self):
        html = """
        <html>
            <body>
                %s
            </body>
        </html>
        """
        payload = 'BOUNDLpayloadBOUNDR'
        contexts = get_context(html % payload.lower(), ('boundl', 'boundr'))
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlText)

    def test_payload_html_inside_comment(self):
        html = """
        <html>
            <!-- <body>boundlPAYLOADboundr</body> -->
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlComment)

    def test_tag_attr_double_quote(self):
        html = """
        <html>
            <tag attr="boundlPAYLOADboundr" />
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrDoubleQuote)

    def test_tag_attr_multiple_payloads_quote(self):
        html = """
        <html>
            <tag attr="{}{}" />
        </html>
        """
        payloads = {'boundlpayloadboundr': 'boundlPAYLOADboundr',
                    'boundlpdboundr': 'boundlPDboundr'}

        html = html.format(*payloads.values())
        contexts = get_context(html, BOUNDARY)

        self.assertEqual(len(contexts), 2)
        self.assertIsInstance(contexts[0], HtmlAttrDoubleQuote)
        self.assertIn(contexts[0].payload, payloads.keys())
        del payloads[contexts[0].payload]
        self.assertIsInstance(contexts[1], HtmlAttrDoubleQuote)
        self.assertIn(contexts[1].payload, payloads.keys())

    def test_tag_attr_multiple_identical_payloads_quote(self):
        html = """
        <html>
            <tag attr="%s%s" />
        </html>
        """
        payload = 'boundlPAYLOADboundr'
        html = html % (payload, payload)
        contexts = get_context(html, BOUNDARY)

        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrDoubleQuote)
        self.assertEqual(contexts[0].payload, payload.lower())

    def test_tag_attr_single_double_quote(self):
        html = """
        <html>
            <tag spam='eggs' attr="boundlPAYLOADboundr" />
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrDoubleQuote)

    def test_payload_a_single_quote(self):
        html = """
        <html>
            <a foo='boundlPAYLOADboundr'>
                bar
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrSingleQuote)

    def test_payload_a_single_quote_with_escape(self):
        html = """
        <html>
            <a foo='boundlPAYLOADboundr&#39;'>
                bar
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrSingleQuote)

    def test_payload_a_double_quote_with_escape(self):
        html = """
        <html>
            <a foo="boundlPAYLOADboundr&quot;">
                bar
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrDoubleQuote)

    def test_payload_backtick(self):
        html = """
        <html>
            <a foo=`boundlPAYLOADboundr`>
                bar
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrBackticks)

    def test_payload_attr_value_no_separator(self):
        html = """
        <html>
            <a foo=boundlPAYLOADboundr bar=loops>
                bar
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlAttrNoQuote)

    def test_payload_in_html_text_complex(self):
        html = """
        <html>
            <tag>foo</tag>
                boundlPAYLOADboundr
            <tag>bar</tag>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlText)

    def test_payload_broken_double_open(self):
        html = """
        <html>
            <tag>foo
                boundlPAYLOADboundr
            <tag>bar</tag>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlText)

    def test_payload_script_broken_double_close(self):
        html = """
        <html>
            <script>foo</script>
                boundlPAYLOADboundr
            </script>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], ScriptText)

    def test_payload_confuse_parser(self):
        html = """
        <html>
            <a attr="</a>">boundlPAYLOADboundr</a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)
        self.assertIsInstance(contexts[0], HtmlText)

    def test_payload_text_with_quotes(self):
        html = """
        <html>
            <a>Quoting the great Linus Torvalds: "boundlPAYLOADboundr<"</a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)

        context = contexts[0]
        self.assertIsInstance(context, HtmlText)
        self.assertFalse(context.can_break())

    def test_payload_text_with_start_quote(self):
        html = """
        <html>
            <a>Quoting the great Linus Torvalds: boundl"PAYLOAD<boundr</a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)

        context = contexts[0]
        self.assertIsInstance(context, HtmlText)

    def test_payload_text_with_end_quote(self):
        html = """
        <html>
            <a>Quoting the great Linus Torvalds: boundlPAYLOAD<"boundr</a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1)

        context = contexts[0]
        self.assertIsInstance(context, HtmlText)

    def test_payload_tag_name(self):
        html = """
        <boundlPAYLOADboundr></x>
        </foo>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)

        self.assertIsInstance(contexts[0], HtmlTag)

    def test_payload_tag_name_close(self):
        html = """
        <foo>
        </boundlPAYLOADboundr>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)

        self.assertIsInstance(contexts[0], HtmlTagClose)

    def test_payload_tag_attr_key(self):
        html = """
        <a boundlPAYLOADboundr="/xyz">foo</a>
        """
        contexts = get_context(html, BOUNDARY)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, HtmlAttr)

    def test_django_500_sample(self):
        html = file(os.path.join(self.SAMPLES_DIR, 'django-500.html')).read()
        contexts = get_context(html, BOUNDARY)
        expected_payload = place_boundary(' =', BOUNDARY)

        self.assertEqual(len(contexts), 9)
        for context in contexts:
            self.assertIsInstance(context, HtmlText)
            self.assertEqual(context.payload, expected_payload)

    def test_payload_html_comment_with_single_quote(self):
        """
        A single quote inside an HTML comment seems to break parsing by
        "extending" the HTML comment context. See the "quote_comment.html"
        file, specifically the section which says:

            "I'm a single quote, and I break stuff."

        Before fixing this bug, if you removed that single quote, this test
        passed.
        """
        html = """
        <!DOCTYPE html>
        <html>
            <!--
            I'm a single quote, and I break stuff.
            -->
            <a href="http://external/abc/boundlPAYLOADboundr">
                Check link href
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)

        self.assertIsInstance(contexts[0], HtmlAttrDoubleQuote)

    def test_payload_html_comment_with_tag_attr_inside(self):
        html = """
        <!DOCTYPE html>
        <html>
            <!--
            <a href="boundlPAYLOADboundr"></a>
            -->
            <a href="http://external/abc/boundlPAYLOADboundr">
                Check link href
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)

        self.assertEqual(len(contexts), 2, contexts)
        self.assertIsInstance(contexts[0], HtmlComment)
        self.assertIsInstance(contexts[1], HtmlAttrDoubleQuote)

    def test_payload_html_comment_with_tag_text_inside(self):
        html = """
        <!DOCTYPE html>
        <html>
            <!--
            <a href="">boundlPAYLOADboundr</a>
            -->
            <a href="http://external/abc/boundlPAYLOADboundr">
            Check link href
            </a>
        </html>
        """
        contexts = get_context(html, BOUNDARY)

        self.assertEqual(len(contexts), 2, contexts)
        self.assertIsInstance(contexts[0], HtmlComment)
        self.assertIsInstance(contexts[1], HtmlAttrDoubleQuote)

    def test_broken_1(self):
        html = """
        <a boundlPAYLOADboundr="/xyz
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 0, contexts)

    def test_broken_2(self):
        html = """
        <a boundlPAYLOADboundr="/xyz" /<
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 0, contexts)

    def test_broken_3(self):
        html = """
        <a boundlPAYLOADboundr="/xyz"><
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        self.assertIsInstance(contexts[0], HtmlAttr)

    def test_broken_4(self):
        html = """
        <a boundlPAYLOADboundr="/xyz"></
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        self.assertIsInstance(contexts[0], HtmlAttr)

    def test_broken_5(self):
        html = """
        <a foo="/xyz"></boundlPAYLOADboundr
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 0, contexts)

    def test_script_text(self):
        html = """
        <script>foo(); bar(boundlPAYLOADboundr);</script>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        self.assertIsInstance(contexts[0], ScriptText)

    def test_style_text(self):
        html = """
        <style>foo(); bar(boundlPAYLOADboundr);</style>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        self.assertIsInstance(contexts[0], CSSText)

    def test_script_text_comment(self):
        html = """
        <script type="text/javascript">
        <!--
        foo(); bar(boundlPAYLOADboundr);
        //-->
        </script>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 1, contexts)
        self.assertIsInstance(contexts[0], ScriptText)

    def test_payload_inside_noscript_1(self):
        html = """
        <html>
            <body>
                <noscript>
                    boundlPAYLOADboundr
                </noscript>
            </body>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 0)

    def test_payload_inside_noscript_2(self):
        html = """
        <html>
            <noscript>
                <a onmouseover="boundlPAYLOADboundr">link</a>
            </noscript>
        </html>
        """
        contexts = get_context(html, BOUNDARY)
        self.assertEqual(len(contexts), 0)
