"""
test_css.py

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
from w3af.core.data.context.tests.context_test import ContextTest
from w3af.core.data.context.context.css import get_css_context
from w3af.core.data.context.context.css import (GenericStyleContext,
                                                StyleSingleQuoteString,
                                                StyleDoubleQuoteString,
                                                StyleComment)


class TestCSSStyle(ContextTest):
    def test_payload_is_all_content(self):
        css_code = 'PAYLOAD:('
        contexts = get_css_context(css_code, css_code)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, GenericStyleContext)
        self.assertTrue(context.can_break())

    def test_payload_is_all_content_no_break(self):
        css_code = 'PAYLOAD'
        contexts = get_css_context(css_code, css_code)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, GenericStyleContext)
        self.assertFalse(context.can_break())

    def test_payload_in_selector(self):
        payload = 'PAYLOAD:('
        css_code = '%s {background-color:lightgray}' % payload
        contexts = get_css_context(css_code, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, GenericStyleContext)
        self.assertTrue(context.can_break())

    def test_payload_in_property(self):
        payload = 'PAYLOAD:('
        css_code = 'body {%s:lightgray}' % payload
        contexts = get_css_context(css_code, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, GenericStyleContext)
        self.assertTrue(context.can_break())

    def test_payload_in_value(self):
        payload = 'PAYLOAD:('
        css_code = 'body {background-color:%s}' % payload
        contexts = get_css_context(css_code, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, GenericStyleContext)
        self.assertTrue(context.can_break())

    def test_payload_value_double_quote_no_break(self):
        # Double quote missing
        payload = 'PAYLOAD:('
        css_code = 'font-family: Georgia, "Times New Roman %s";' % payload
        contexts = get_css_context(css_code, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, StyleDoubleQuoteString)
        self.assertFalse(context.can_break())

    def test_payload_value_double_quote_break(self):
        payload = 'PAYLOAD:("'
        css_code = 'font-family: Georgia, "Times New Roman %s";' % payload
        contexts = get_css_context(css_code, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, StyleDoubleQuoteString)
        self.assertTrue(context.can_break())

    def test_payload_value_single_quote(self):
        payload = "PAYLOAD:('"
        css_code = "background: url('%s')" % payload
        contexts = get_css_context(css_code, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, StyleSingleQuoteString)
        self.assertTrue(context.can_break())

    def test_payload_in_comment_no_break(self):
        payload = 'PAYLOAD'
        css_code = '''
        p {
            color: red;
            /* This is a single-line %s comment */
            text-align: center;
        }
        '''
        contexts = get_css_context(css_code % payload, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, StyleComment)
        self.assertFalse(context.can_break())

    def test_payload_in_comment_break(self):
        payload = 'PAYLOAD*/:('
        css_code = '''
        p {
            color: red;
            /* This is a single-line %s comment */
            text-align: center;
        }
        '''
        contexts = get_css_context(css_code % payload, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, StyleComment)
        self.assertTrue(context.can_break())

    def test_comment_false_positive(self):
        payload = 'PAYLOAD'
        css_code = '''
        p {
            color: red;
            background: url('/* This is a false positive test %s */');
            text-align: center;
        }
        '''
        contexts = get_css_context(css_code % payload, payload)

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, StyleSingleQuoteString)
        self.assertFalse(context.can_break())
