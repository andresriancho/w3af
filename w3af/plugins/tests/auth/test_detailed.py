"""
test_detailed.py

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
from httpretty import httpretty

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.ci.moth import get_moth_http


class TestDetailedBasic(PluginTest):

    target_url = get_moth_http('/auth/auth_1/')
    
    auth_url = URL(target_url + 'login_form.py')
    check_url = URL(target_url + 'post_auth_xss.py')
    check_string = 'or read your input'
    data_format = '%u=%U&%p=%P&Login=Login'
    
    _run_config = {
        'target': target_url,
        'plugins': {
        'crawl': (
            PluginConfig('web_spider',
                         ('only_forward', True, PluginConfig.BOOL),
                         ('ignore_regex', '.*logout.*', PluginConfig.STR)),

            ),
            'audit': (PluginConfig('xss',),),
            'auth': (PluginConfig('detailed',
                                 ('username', 'user@mail.com', PluginConfig.STR),
                                 ('password', 'passw0rd', PluginConfig.STR),
                                 ('username_field', 'username', PluginConfig.STR),
                                 ('password_field', 'password', PluginConfig.STR),
                                 ('data_format', data_format, PluginConfig.STR),
                                 ('auth_url', auth_url, PluginConfig.URL),
                                 ('method', 'POST', PluginConfig.STR),
                                 ('check_url', check_url, PluginConfig.URL),
                                 ('check_string', check_string, PluginConfig.STR),
                                 ('follow_redirects', False, PluginConfig.BOOL),
                                  ),
                         ),
        }
    }

    def test_post_auth_xss(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        vulns = self.kb.get('xss', 'xss')

        self.assertEquals(len(vulns), 1, vulns)

        vuln = vulns[0]
        self.assertEquals(vuln.get_name(), 'Cross site scripting vulnerability')
        self.assertEquals(vuln.get_token_name(), 'text')


class TestDetailedRedirect(PluginTest):

    target_url = 'http://mock/auth/'

    auth_url = URL(target_url + 'login_form.py')
    check_url = URL(target_url + 'verify.py')
    check_string = 'Logged in'
    data_format = '%u=%U&%p=%P&Login=Login'

    MOCK_RESPONSES = [MockResponse('http://mock/auth/login_form.py', '',
                                   status=302,
                                   headers={'Location': '/confirm/?token=123'},
                                   method='POST'),
                      MockResponse('http://mock/confirm/?token=123',
                                   'Login success',
                                   status=302,
                                   headers={'Location': '/auth/home.py'}),
                      MockResponse('http://mock/auth/home.py', 'Home page'),
                      MockResponse('http://mock/auth/verify.py',
                                   'Not logged in')]

    _run_config = {
        'target': target_url,
        'plugins': {
            'audit': (PluginConfig('xss'),),
            'auth': (PluginConfig('detailed',
                                 ('username', 'user@mail.com', PluginConfig.STR),
                                 ('password', 'passw0rd', PluginConfig.STR),
                                 ('username_field', 'username', PluginConfig.STR),
                                 ('password_field', 'password', PluginConfig.STR),
                                 ('data_format', data_format, PluginConfig.STR),
                                 ('auth_url', auth_url, PluginConfig.URL),
                                 ('method', 'POST', PluginConfig.STR),
                                 ('check_url', check_url, PluginConfig.URL),
                                 ('check_string', check_string, PluginConfig.STR),
                                 ('follow_redirects', True, PluginConfig.BOOL),),),
        }
    }

    def test_redirect_login(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        all_paths = set()
        for request in httpretty.latest_requests:
            all_paths.add(request.path)

        # Followed two redirects
        self.assertIn('/confirm/?token=123', all_paths)
        self.assertIn('/auth/home.py', all_paths)

        # Send the POST to login
        self.assertIn('/auth/login_form.py', all_paths)


class TestDetailedRedirectLoop(PluginTest):

    target_url = 'http://mock/auth/'

    auth_url = URL(target_url + 'login_form.py')
    check_url = URL(target_url + 'verify.py')
    check_string = 'Logged in'
    data_format = '%u=%U&%p=%P&Login=Login'

    MOCK_RESPONSES = [MockResponse('http://mock/auth/login_form.py', '',
                                   status=302,
                                   headers={'Location': '/confirm/?token=123'},
                                   method='POST'),

                      # Redirect loop #1
                      MockResponse('http://mock/confirm/?token=123',
                                   'Created new token',
                                   status=302,
                                   headers={'Location': '/confirm/?token=abc'}),

                      # Redirect loop #2
                      MockResponse('http://mock/confirm/?token=abc',
                                   'Token is not new',
                                   status=302,
                                   headers={'Location': '/confirm/?token=123'}),

                      MockResponse('http://mock/auth/home.py', 'Home page'),
                      MockResponse('http://mock/auth/verify.py', 'Not logged in')]

    _run_config = {
        'target': target_url,
        'plugins': {
            'audit': (PluginConfig('xss'),),
            'auth': (PluginConfig('detailed',
                                 ('username', 'user@mail.com', PluginConfig.STR),
                                 ('password', 'passw0rd', PluginConfig.STR),
                                 ('username_field', 'username', PluginConfig.STR),
                                 ('password_field', 'password', PluginConfig.STR),
                                 ('data_format', data_format, PluginConfig.STR),
                                 ('auth_url', auth_url, PluginConfig.URL),
                                 ('method', 'POST', PluginConfig.STR),
                                 ('check_url', check_url, PluginConfig.URL),
                                 ('check_string', check_string, PluginConfig.STR),
                                 ('follow_redirects', True, PluginConfig.BOOL),),),
        }
    }

    def test_redirect_loop_in_login(self):
        """
        The main test here is that the plugin finishes
        """
        self._scan(self._run_config['target'], self._run_config['plugins'])

        all_paths = set()
        for request in httpretty.latest_requests:
            all_paths.add(request.path)

        # Followed two redirects which are in a loop
        self.assertIn('/confirm/?token=123', all_paths)
        self.assertIn('/confirm/?token=abc', all_paths)

        # Send the POST to login
        self.assertIn('/auth/login_form.py', all_paths)


class TestDetailedSquareBrackets(PluginTest):
    """
    :see: https://github.com/andresriancho/w3af/issues/5593
    """
    target_url = get_moth_http('/auth/')

    auth_url = URL(get_moth_http('/auth/auth_2/square_bracket_login_form.py'))
    check_url = URL(get_moth_http('/auth/auth_1/post_auth_xss.py'))
    check_string = 'or read your input'
    data_format = '%u=%U&%p=%P&Login=Login'

    _run_config = {
        'target': target_url,
        'plugins': {
        'crawl': (
            PluginConfig('web_spider',
                         ('only_forward', True, PluginConfig.BOOL),
                         ('ignore_regex', '.*logout.*', PluginConfig.STR)),

            ),
            'audit': (PluginConfig('xss',),),
            'auth': (PluginConfig('detailed',
                                 ('username', 'user@mail.com', PluginConfig.STR),
                                 ('password', 'passw0rd', PluginConfig.STR),
                                 # Check this foo[user] setting! This is what we
                                 # want to test
                                 ('username_field', 'foo[user]', PluginConfig.STR),
                                 ('password_field', 'password', PluginConfig.STR),
                                 ('data_format', data_format, PluginConfig.STR),
                                 ('auth_url', auth_url, PluginConfig.URL),
                                 ('method', 'POST', PluginConfig.STR),
                                 ('check_url', check_url, PluginConfig.URL),
                                 ('check_string', check_string, PluginConfig.STR),
                                 ('follow_redirects', False, PluginConfig.BOOL),
                                  ),
                         ),
        }
    }

    def test_post_auth_xss(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        vulns = self.kb.get('xss', 'xss')

        self.assertEquals(len(vulns), 1, vulns)

        vuln = vulns[0]
        self.assertEquals(vuln.get_name(), 'Cross site scripting vulnerability')
        self.assertEquals(vuln.get_token_name(), 'text')

