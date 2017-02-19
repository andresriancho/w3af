# -*- coding: UTF-8 -*-
"""
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
import re
import json
import unittest
from w3af.core.data.parsers.utils.form_id_matcher import FormIDMatcher


class TestFormIDMatcher(unittest.TestCase):
    def test_form_id_matcher_trivial(self):
        action = re.compile('/comments')
        hosted_at_url = re.compile('/products/.*')

        form_idm = FormIDMatcher(hosted_at_url=hosted_at_url,
                                 inputs=['comment'],
                                 action=action,
                                 attributes={'class': 'comment-css'})

        self.assertEqual(form_idm.hosted_at_url, hosted_at_url)
        self.assertEqual(form_idm.inputs, ['comment'])
        self.assertEqual(form_idm.action, action)
        self.assertEqual(form_idm.attributes, {'class': 'comment-css'})

    def test_form_id_matcher_from_json(self):
        json_string = json.dumps({'hosted_at_url': '/products/.*',
                                  'action': '/comments',
                                  'attributes': {'class': 'comment-css'},
                                  'inputs': ['comment'],
                                  'method': 'get'})
        form_idm = FormIDMatcher.from_json(json_string)

        self.assertIsInstance(form_idm.hosted_at_url, re._pattern_type)
        self.assertIsInstance(form_idm.action, re._pattern_type)
        self.assertEqual(form_idm.inputs, ['comment'])
        self.assertEqual(form_idm.attributes, {'class': 'comment-css'})
        self.assertEqual(form_idm.method, 'get')

    def test_form_id_matcher_from_json_missing_is_none_hosted(self):
        json_string = json.dumps({'action': '/comments',
                                  'attributes': {'class': 'comment-css'},
                                  'inputs': ['comment']})
        form_idm = FormIDMatcher.from_json(json_string)

        self.assertIsNone(form_idm.hosted_at_url)
        self.assertIsInstance(form_idm.action, re._pattern_type)
        self.assertEqual(form_idm.inputs, ['comment'])
        self.assertEqual(form_idm.attributes, {'class': 'comment-css'})

    def test_form_id_matcher_from_json_missing_is_none_attr(self):
        json_string = json.dumps({'action': '/comments',
                                  'inputs': ['comment']})
        form_idm = FormIDMatcher.from_json(json_string)

        self.assertIsNone(form_idm.hosted_at_url)
        self.assertIsInstance(form_idm.action, re._pattern_type)
        self.assertEqual(form_idm.inputs, ['comment'])
        self.assertIsNone(form_idm.attributes)

    def test_form_id_matcher_all_none(self):
        json_string = json.dumps({})
        form_idm = FormIDMatcher.from_json(json_string)

        self.assertIsNone(form_idm.hosted_at_url)
        self.assertIsNone(form_idm.action)
        self.assertIsNone(form_idm.inputs)
        self.assertIsNone(form_idm.attributes)

    def test_invalid_structure_1(self):
        # Note the invalid regular expression in hosted_at_url
        json_string = json.dumps({'hosted_at_url': '/products/.(*',
                                  'action': '/comments',
                                  'attributes': {'class': 'comment-css'},
                                  'inputs': ['comment']})
        self.assertRaises(ValueError, FormIDMatcher.from_json, json_string)

    def test_invalid_structure_2(self):
        # Note the list in action
        json_string = json.dumps({'hosted_at_url': '/products/.*',
                                  'action': [],
                                  'attributes': {'class': 'comment-css'},
                                  'inputs': ['comment']})
        self.assertRaises(ValueError, FormIDMatcher.from_json, json_string)

    def test_invalid_structure_3(self):
        # Note the dict in inputs
        json_string = json.dumps({'hosted_at_url': '/products/.*',
                                  'action': [],
                                  'attributes': {'class': 'comment-css'},
                                  'inputs': {}})
        self.assertRaises(ValueError, FormIDMatcher.from_json, json_string)
