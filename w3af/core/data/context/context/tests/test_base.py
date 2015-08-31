"""
test_base.py

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

from w3af.core.data.context.context.base import BaseContext


class TestBaseContext(unittest.TestCase):

    def test_is_inside_context_1(self):
        html = '<html>abc</html>'
        context_start = '<html>'
        context_end = '</html>'
        self.assertFalse(BaseContext.is_inside_context(html,
                                                       context_start,
                                                       context_end))

    def test_is_inside_context_2(self):
        html = '<html>abc'
        context_start = '<html>'
        context_end = '</html>'
        self.assertTrue(BaseContext.is_inside_context(html,
                                                      context_start,
                                                      context_end))

    def test_is_inside_context_3(self):
        html = '<tag attr="'
        context_start = '"'
        context_end = '"'
        self.assertTrue(BaseContext.is_inside_context(html,
                                                      context_start,
                                                      context_end))

    def test_is_inside_context_4(self):
        html = '<tag>abc</tag><tag>def'
        context_start = '<tag>'
        context_end = '</tag>'
        self.assertTrue(BaseContext.is_inside_context(html,
                                                      context_start,
                                                      context_end))

    def test_get_context_content_1(self):
        html = '<html>abc'
        context_start = '<html>'
        context_end = '</html>'
        content = BaseContext.get_context_content(html, context_start,
                                                  context_end)

        self.assertEqual(content, 'abc')

    def test_get_context_content_2(self):
        html = '<script type="application/json">foo;PAYLOAD'
        context_start = '<script'
        context_end = '</script>'
        content = BaseContext.get_context_content(html, context_start,
                                                  context_end,
                                                  context_start_cut='>')

        self.assertEqual(content, 'foo;PAYLOAD')

    def test_get_context_content_3(self):
        html = '<a href="foo();PAYLOAD'
        context_start = '"'
        context_end = '"'
        content = BaseContext.get_context_content(html, context_start,
                                                  context_end)

        self.assertEqual(content, 'foo();PAYLOAD')

    def test_get_context_content_4(self):
        html = "<a href='foo();PAYLOAD"
        context_start = "'"
        context_end = "'"
        content = BaseContext.get_context_content(html, context_start,
                                                  context_end)

        self.assertEqual(content, 'foo();PAYLOAD')

    def test_get_attr_name_1(self):
        html = "<a href='"
        attr_delim = "'"
        attr_name = BaseContext.get_attr_name(html, attr_delim)

        self.assertEqual(attr_name, 'href')

    def test_get_attr_name_2(self):
        html = "<a href= '"
        attr_delim = "'"
        attr_name = BaseContext.get_attr_name(html, attr_delim)

        self.assertEqual(attr_name, 'href')

    def test_get_attr_name_3(self):
        html = "<a href = '"
        attr_delim = "'"
        attr_name = BaseContext.get_attr_name(html, attr_delim)

        self.assertEqual(attr_name, 'href')

    def test_get_attr_name_4(self):
        html = "<a href     =  '"
        attr_delim = "'"
        attr_name = BaseContext.get_attr_name(html, attr_delim)

        self.assertEqual(attr_name, 'href')

    def test_is_inside_html_comment_1(self):
        html = "<a href='/foo'><!--"
        self.assertTrue(BaseContext.is_inside_html_comment(html))

    def test_is_inside_html_comment_2(self):
        html = "<a href='/foo'><!-- a -->"
        self.assertFalse(BaseContext.is_inside_html_comment(html))

    def test_is_inside_html_comment_3(self):
        html = "<a href='/foo'><!-- \n a "
        self.assertTrue(BaseContext.is_inside_html_comment(html))

    def test_is_inside_nested_contexts_1(self):
        html = "<a href = '"
        context_starts = ['<a', "'"]
        context_ends = ['</a>', "'"]

        self.assertTrue(BaseContext.is_inside_nested_contexts(html,
                                                              context_starts,
                                                              context_ends))

    def test_is_inside_nested_contexts_2(self):
        # Double quote here
        html = '<a href="'

        # Single quotes here
        context_starts = ['<a', "'"]
        context_ends = ['</a>', "'"]

        self.assertFalse(BaseContext.is_inside_nested_contexts(html,
                                                               context_starts,
                                                               context_ends))

    def test_is_inside_nested_contexts_3(self):
        # Order is reversed
        html = 'The great double quote at " <a'
        context_starts = ['<a', '"']
        context_ends = ['</a>', '"']

        self.assertFalse(BaseContext.is_inside_nested_contexts(html,
                                                               context_starts,
                                                               context_ends))
