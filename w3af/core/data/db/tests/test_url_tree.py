# -*- coding: UTF-8 -*-
"""
Copyright 2018 Andres Riancho

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

from w3af.core.data.db.url_tree import URLTree, url_tree_factory
from w3af.core.data.parsers.doc.url import URL


class TestURLTree(unittest.TestCase):
    def test_empty(self):
        tree = URLTree()
        self.assertEqual(tree.tree, {})

    def test_root(self):
        tree = URLTree()

        url = URL('http://w3af.org/')
        tree.add_url(url)

        expected = url_tree_factory()
        expected[u'http://w3af.org']

        self.assertEqual(tree.tree, expected)

    def test_two_independent_paths(self):
        tree = URLTree()

        url_1 = URL('http://w3af.org/foo/')
        url_2 = URL('http://w3af.org/bar/')
        tree.add_url(url_1)
        tree.add_url(url_2)

        expected = url_tree_factory()
        expected[u'http://w3af.org'][u'foo']
        expected[u'http://w3af.org'][u'bar']

        self.assertEqual(tree.tree, expected)

    def test_two_nested_paths(self):
        tree = URLTree()

        url_1 = URL('http://w3af.org/foo/bar/')
        url_2 = URL('http://w3af.org/spam/eggs/')
        tree.add_url(url_1)
        tree.add_url(url_2)

        expected = url_tree_factory()
        expected[u'http://w3af.org'][u'foo'][u'bar']
        expected[u'http://w3af.org'][u'spam'][u'eggs']

        self.assertEqual(tree.tree, expected)

    def test_nested_paths_and_files(self):
        tree = URLTree()

        url_1 = URL('http://w3af.org/foo/bar/')
        url_2 = URL('http://w3af.org/spam/eggs/123.txt')
        tree.add_url(url_1)
        tree.add_url(url_2)

        expected = url_tree_factory()
        expected[u'http://w3af.org'][u'foo'][u'bar']
        expected[u'http://w3af.org'][u'spam'][u'eggs'][u'123.txt']

        self.assertEqual(tree.tree, expected)

