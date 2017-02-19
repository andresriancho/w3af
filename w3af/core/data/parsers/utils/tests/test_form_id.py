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
import json
import unittest

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_id import FormID
from w3af.core.data.parsers.utils.form_id_matcher import FormIDMatcher
from w3af.core.data.parsers.utils.form_id_matcher_list import FormIDMatcherList


class TestFormID(unittest.TestCase):
    HOSTED_AT_URL = URL('http://w3af.org/products/product-132')
    ACTION_URL = URL('http://w3af.org/products/comments')

    def test_form_id_trivial(self):
        form_id = FormID(hosted_at_url=self.HOSTED_AT_URL,
                         inputs=['comment'],
                         action=self.ACTION_URL,
                         attributes={'class': 'comment-css'},
                         method='get')

        self.assertEqual(form_id.hosted_at_url, self.HOSTED_AT_URL)
        self.assertEqual(form_id.inputs, ['comment'])
        self.assertEqual(form_id.action, self.ACTION_URL)
        self.assertEqual(form_id.attributes, {'class': 'comment-css'})
        self.assertEqual(form_id.method, 'get')

    def test_form_id_to_json(self):
        form_id = FormID(hosted_at_url=self.HOSTED_AT_URL,
                         inputs=['comment'],
                         action=self.ACTION_URL,
                         attributes={'class': 'comment-css'},
                         method='post')

        form_id_json = form_id.to_json()
        loaded_form_id = json.loads(form_id_json)

        self.assertEqual(loaded_form_id['action'], form_id.action.get_path())
        self.assertEqual(loaded_form_id['hosted_at_url'], form_id.hosted_at_url.get_path())
        self.assertEqual(loaded_form_id['inputs'], form_id.inputs)
        self.assertEqual(loaded_form_id['attributes'], form_id.attributes)
        self.assertEqual(loaded_form_id['method'], form_id.method)

    def create_form_matcher(self, form_matcher_data):
        json_data = json.dumps(form_matcher_data)
        return FormIDMatcher.from_json(json_data)

    def test_match_all(self):
        user_configured_json = {'hosted_at_url': '/products/.*',
                                'inputs': ['comment'],
                                'action': '/products/comments',
                                'attributes': {'class': 'comment-css'}}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'],
                               hosted_at_url=self.HOSTED_AT_URL,
                               attributes={'class': 'comment-css'})

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_match_empty_user_configured_json(self):
        user_configured_json = {}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_match_method(self):
        user_configured_json = {'method': 'get'}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'],
                               method='get')

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_not_match_method(self):
        user_configured_json = {'method': 'get'}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'],
                               method='post')

        match = found_form_id.matches(form_matcher)

        self.assertFalse(match)

    def test_match_action_regex(self):
        user_configured_json = {'action': '/products/comm.*'}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_match_action_regex_input_partial(self):
        user_configured_json = {'action': '/products/comm.*',
                                'inputs': ['comment']}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_match_action_regex_input_all(self):
        user_configured_json = {'action': '/products/comm.*',
                                'inputs': ['comment', 'submit']}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_match_action_regex_not_input_extra(self):
        user_configured_json = {'action': '/products/comm.*',
                                'inputs': ['comment', 'special', 'submit']}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertFalse(match)

    def test_no_match_when_action_regex_match_and_input_not(self):
        user_configured_json = {'action': '/products/comm.*',
                                'inputs': ['foo']}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertFalse(match)

    def test_match_hosted_at_regex(self):
        user_configured_json = {'hosted_at_url': '/products/.*'}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(hosted_at_url=self.HOSTED_AT_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_not_match_hosted_at_regex(self):
        user_configured_json = {'hosted_at_url': '/products/.*'}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(hosted_at_url=URL('http://w3af.org/another/product-132'),
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertFalse(match)

    def test_match_hosted_at_regex_inputs(self):
        user_configured_json = {'hosted_at_url': '/products/.*',
                                'inputs': ['comment']}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(hosted_at_url=self.HOSTED_AT_URL,
                               inputs=['comment', 'submit'])

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_match_attrs(self):
        user_configured_json = {'attributes': {'class': 'comment-css'}}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'],
                               hosted_at_url=self.HOSTED_AT_URL,
                               attributes={'class': 'comment-css'})

        match = found_form_id.matches(form_matcher)

        self.assertTrue(match)

    def test_not_match_attrs(self):
        user_configured_json = {'attributes': {'class': 'impact-css'}}
        form_matcher = self.create_form_matcher(user_configured_json)
        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'],
                               hosted_at_url=self.HOSTED_AT_URL,
                               attributes={'class': 'comment-css'})

        match = found_form_id.matches(form_matcher)

        self.assertFalse(match)

    def test_matches_one_of_false_1(self):
        user_value = '[{"action": "/foo"}, {"action": "/bar", "method": "get"}]'
        form_list = FormIDMatcherList(user_value)

        found_form_id = FormID(action=self.ACTION_URL,
                               inputs=['comment', 'submit'],
                               hosted_at_url=self.HOSTED_AT_URL,
                               attributes={'class': 'comment-css'})

        match = found_form_id.matches_one_of(form_list)

        self.assertFalse(match)

    def test_matches_one_of_false_2(self):
        user_value = '[{"action": "/foo", "method": "post"}, {"action": "/products/product-.*", "method": "get"}]'
        form_list = FormIDMatcherList(user_value)

        found_form_id = FormID(action=URL('http://w3af.org/products/product-132'),
                               inputs=['comment', 'submit'],
                               hosted_at_url=self.HOSTED_AT_URL,
                               method='post',
                               attributes={'class': 'comment-css'})

        match = found_form_id.matches_one_of(form_list)

        self.assertFalse(match)

    def test_matches_one_of_true(self):
        user_value = '[{"action": "/foo", "method": "post"}, {"action": "/products/product-.*", "method": "get"}]'
        form_list = FormIDMatcherList(user_value)

        found_form_id = FormID(action=URL('http://w3af.org/products/product-132'),
                               inputs=['comment', 'submit'],
                               hosted_at_url=self.HOSTED_AT_URL,
                               method='get',
                               attributes={'class': 'comment-css'})

        match = found_form_id.matches_one_of(form_list)

        self.assertTrue(match)
