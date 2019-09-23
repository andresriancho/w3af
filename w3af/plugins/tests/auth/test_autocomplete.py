"""
test_autocomplete.py

Copyright 2019 Andres Riancho

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
from httpretty import httpretty

import w3af.core.data.kb.knowledge_base as kb

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.data.parsers.doc.url import URL

USER = 'user@mail.com'
PASS = 'passw0rd'

HTML_LOGIN_FORM = """\
<html>
    <form action="/login_post.py" method="POST">
        <input type="text" name="user" />
        <input type="password" name="password" />
        <input type="hidden" name="__csrf" value="11223344aabbccdd" />
        <input type="submit"/>
    </form>
</html>
"""

SUCCESS = False


class LoginMockResponse(MockResponse):
    def get_response(self, http_request, uri, response_headers):
        #
        # Check the form parameter and the cookie
        #
        if http_request.parsed_body['__csrf'][0] != '11223344aabbccdd':
            return 403, response_headers, 'CSRF'

        if '09876xyzxyz' not in http_request.headers.get('Cookie'):
            return 403, response_headers, 'Missing cookie'

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
        response_headers['Location'] = 'http://w3af.org/admin'
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

        response_headers['Location'] = 'http://w3af.org/unittest'
        response_headers['status'] = 302

        global SUCCESS
        SUCCESS = True

        return 302, response_headers, 'Logged in'


class TestAutocomplete(PluginTest):
    target_url = 'http://w3af.org/'

    login_form_url = URL(target_url + 'login_form.py')
    login_post_handler_url = URL(target_url + 'login_post.py')

    check_url = URL(target_url + 'admin')
    check_string = 'Logged in'

    MOCK_RESPONSES = [
                      MockResponse('http://w3af.org/login_form.py',
                                   HTML_LOGIN_FORM,
                                   status=200,
                                   method='GET',
                                   headers={'Set-Cookie': '__csrf=09876xyzxyz'}),

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
            'auth': (PluginConfig('autocomplete',
                                  ('username', USER, PluginConfig.STR),
                                  ('password', PASS, PluginConfig.STR),
                                  ('login_form_url', login_form_url, PluginConfig.URL),
                                  ('check_url', check_url, PluginConfig.URL),
                                  ('check_string', check_string, PluginConfig.STR)),),
        }
    }

    def test_find_form_submit_csrf_token(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        all_paths = set()
        for request in httpretty.latest_requests:
            all_paths.add(request.path)

        self.assertIn('/login_form.py', all_paths)
        self.assertIn('/login_post.py', all_paths)
        self.assertIn('/admin', all_paths)

        self.assertTrue(SUCCESS)
        #self.assertIn('/unittest', all_paths)


class TestAutocompleteInvalidCredentials(PluginTest):
    target_url = 'http://w3af.org/'

    login_form_url = URL(target_url + 'login_form.py')
    login_post_handler_url = URL(target_url + 'login_post.py')

    check_url = URL(target_url + 'admin')
    check_string = 'Logged in'

    MOCK_RESPONSES = [
                      MockResponse('http://w3af.org/login_form.py',
                                   HTML_LOGIN_FORM,
                                   status=200,
                                   method='GET',
                                   headers={'Set-Cookie': '__csrf=09876xyzxyz'}),

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
            'auth': (PluginConfig('autocomplete',
                                  ('username', USER, PluginConfig.STR),
                                  #
                                  # The login process fails because of this invalid password
                                  #
                                  ('password', PASS + 'invalid', PluginConfig.STR),
                                  ('login_form_url', login_form_url, PluginConfig.URL),
                                  ('check_url', check_url, PluginConfig.URL),
                                  ('check_string', check_string, PluginConfig.STR)),),
        }
    }

    def test_handle_invalid_credentials(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        infos = kb.kb.get('authentication', 'error')

        self.assertEqual(len(infos), 1)
        info = infos[0]

        expected_desc = (
            'The authentication plugin failed to get a valid application session using the user-provided configuration settings.\n'
            '\n'
            'The plugin generated the following log messages:\n'
            '\n'
            'Logging into the application with user: user@mail.com\n'
            'Login form with action http://w3af.org/login_post.py found in HTTP response with ID 21\n'
            'Login form sent to http://w3af.org/login_post.py in HTTP request ID 22\n'
            'Checking if session for user user@mail.com is active\n'
            'User "user@mail.com" is NOT logged into the application, the `check_string` was not found in the HTTP response with ID 23.'
        )

        self.assertEqual(info.get_name(), 'Authentication failure')
        self.assertEqual(info.get_desc(with_id=False), expected_desc)
        self.assertEqual(info.get_id(), [21, 22, 23])
