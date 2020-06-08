"""
test_javascript.py

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
from w3af.core.data.context.context.javascript import get_js_context
from w3af.core.data.context.context.javascript import (ScriptExecutableContext,
                                                       ScriptSingleQuoteString,
                                                       ScriptDoubleQuoteString,
                                                       ScriptSingleLineComment,
                                                       ScriptMultiLineComment)


class TestJavaScript(ContextTest):
    def test_payload_is_all_content(self):
        js_code = 'PAYLOAD'
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptExecutableContext)
        self.assertTrue(context.is_executable())

    def test_payload_is_executable_1(self):
        js_code = 'alert("Hello " + PAYLOAD);'
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptExecutableContext)
        self.assertTrue(context.is_executable())

    def test_payload_is_executable_2(self):
        js_code = "init({login:'',foo: PAYLOAD})"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptExecutableContext)
        self.assertTrue(context.is_executable())

    def test_payload_is_executable_3(self):
        js_code = "alert('Hello'); PAYLOAD;"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptExecutableContext)
        self.assertTrue(context.is_executable())

    def test_payload_is_executable_4(self):
        js_code = "PAYLOAD; alert('Hello');"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptExecutableContext)
        self.assertTrue(context.is_executable())

    def test_payload_break_single_quote_1(self):
        js_code = "init({login:'',foo: 'PAYLOAD'})"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptSingleQuoteString)
        self.assertFalse(context.is_executable())

    def test_payload_break_single_quote_2(self):
        js_code = "alert('PAYLOAD');"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptSingleQuoteString)
        self.assertFalse(context.is_executable())

    def test_payload_break_single_quote_3(self):
        js_code = "alert('Hello ' + 'PAYLOAD');"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptSingleQuoteString)
        self.assertFalse(context.is_executable())

    def test_single_quote_escape(self):
        js_code = "alert('Hello \\' world' + PAYLOAD);"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptExecutableContext)
        self.assertTrue(context.is_executable())

    def test_single_quote_mix_double(self):
        js_code = "alert('Hello' + \"PAYLOAD\");"
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptDoubleQuoteString)
        self.assertFalse(context.is_executable())

    def test_payload_break_double_quote_1(self):
        js_code = 'init({login:'',foo: "PAYLOAD"})'
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptDoubleQuoteString)
        self.assertFalse(context.is_executable())

    def test_payload_break_double_quote_2(self):
        js_code = 'alert("PAYLOAD");'
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptDoubleQuoteString)
        self.assertFalse(context.is_executable())

    def test_payload_break_double_quote_3(self):
        js_code = 'alert("Hello " + "PAYLOAD");'
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptDoubleQuoteString)
        self.assertFalse(context.is_executable())

    def test_payload_break_single_line_comment(self):
        js_code = """
        foo();
        // PAYLOAD
        bar();
        """
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptSingleLineComment)
        self.assertFalse(context.is_executable())

    def test_payload_break_single_line_comment_false_positive(self):
        js_code = """
        foo('// PAYLOAD');
        """
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptSingleQuoteString)
        self.assertFalse(context.is_executable())

    def test_payload_break_single_line_comment_with_single_quote(self):
        js_code = """
        foo();
        // I\'m a single quote and I break stuff PAYLOAD
        bar();
        """
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptSingleLineComment)
        self.assertFalse(context.is_executable())

    def test_payload_break_multi_line_comment(self):
        js_code = """
        foo('');
        /*
        Multi
        Line
        PAYLOAD
        Comments
        */
        bar();
        """
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptMultiLineComment)
        self.assertFalse(context.is_executable())

    def test_payload_break_multi_line_comment_false_positive(self):
        js_code = """
        foo('/* PAYLOAD');
        """
        contexts = get_js_context(js_code, 'PAYLOAD')

        self.assertEqual(len(contexts), 1, contexts)
        context = contexts[0]

        self.assertIsInstance(context, ScriptSingleQuoteString)
        self.assertFalse(context.is_executable())
