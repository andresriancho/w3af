"""
test_autocomplete_js.py

Copyright 2020 Andres Riancho

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
import unittest

from httpretty import httpretty
from mock import Mock

import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.plugins.auth.autocomplete import autocomplete
from w3af.core.data.parsers.doc.url import URL

VANILLA_JS_LOGIN = os.path.join(ROOT_PATH, 'plugins/tests/auth/autocomplete_js/vanilla_javascript_1/index.html')
VANILLA_JS_LOGIN = file(VANILLA_JS_LOGIN).read()

USER = 'user@mail.com'
PASS = 'passw0rd'


class LoginMockResponse(MockResponse):
    def get_response(self, http_request, uri, response_headers):
        #
        # Check username and password
        #
        if http_request.parsed_body.get('user')[0] != USER:
            return 403, response_headers, 'Invalid user'

        if http_request.parsed_body.get('password')[0] != PASS:
            return 403, response_headers, 'Invalid password'

        #
        # Build the response
        #
        response_headers['Set-Cookie'] = 'session=naming_is_hard'
        response_headers['Location'] = '/admin'
        response_headers['status'] = 302

        return self.status, response_headers, 'Success!'


class SessionCheckMockResponse(MockResponse):
    def get_response(self, http_request, uri, response_headers):
        #
        # Check the session cookie
        #
        cookie = http_request.headers.get('Cookie')

        if not cookie:
            return 403, response_headers, 'Forbidden'

        if 'naming_is_hard' not in cookie:
            return 403, response_headers, 'Forbidden'

        response_headers['Location'] = '/unittest'
        response_headers['status'] = 302

        return 302, response_headers, 'Logged in'


class TestAutocompleteJavaScript(PluginTest):
    target_url = 'http://w3af.org/'

    login_form_url = URL(target_url + 'login_form.py')
    login_post_handler_url = URL(target_url + 'login_post.py')

    check_url = URL(target_url + 'admin')
    check_string = 'Logged in'

    MOCK_RESPONSES = [
                      MockResponse('http://w3af.org/login_form.py',
                                   VANILLA_JS_LOGIN,
                                   status=200,
                                   method='GET'),

                      LoginMockResponse('http://w3af.org/login_post.py',
                                        '',
                                        method='POST'),

                      SessionCheckMockResponse('http://w3af.org/admin', ''),

                      MockResponse('http://w3af.org/unittest',
                                   'Success',
                                   status=200,
                                   method='GET')
                      ]

    _run_config = {
        'target': target_url,
        'plugins': {
            'audit': (PluginConfig('xss'),),
            'auth': (PluginConfig('autocomplete_js',
                                  ('username', USER, PluginConfig.STR),
                                  ('password', PASS, PluginConfig.STR),
                                  ('login_form_url', login_form_url, PluginConfig.URL),
                                  ('check_url', check_url, PluginConfig.URL),
                                  ('check_string', check_string, PluginConfig.STR)),),
        }
    }

    def test_find_form_submit_login_check(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        all_paths = set()
        for request in httpretty.latest_requests:
            all_paths.add(request.path)

        self.assertIn('/login_form.py', all_paths)
        self.assertIn('/login_post.py', all_paths)
        self.assertIn('/admin', all_paths)
        self.assertIn('/unittest', all_paths)
