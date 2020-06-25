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

from urlparse import urlparse
from urlparse import parse_qs

import pytest

from w3af import ROOT_PATH
from w3af.plugins.auth.autocomplete_js import autocomplete_js
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.data.parsers.doc.url import URL

VANILLA_JS_LOGIN_1 = os.path.join(ROOT_PATH, 'plugins/tests/auth/autocomplete_js/vanilla_javascript_1/index.html')
VANILLA_JS_LOGIN_1 = file(VANILLA_JS_LOGIN_1).read()

VANILLA_JS_LOGIN_2 = os.path.join(ROOT_PATH, 'plugins/tests/auth/autocomplete_js/vanilla_javascript_2/index.html')
VANILLA_JS_LOGIN_2 = file(VANILLA_JS_LOGIN_2).read()

VANILLA_JS_LOGIN_3 = os.path.join(ROOT_PATH, 'plugins/tests/auth/autocomplete_js/vanilla_javascript_3/index.html')
VANILLA_JS_LOGIN_3 = file(VANILLA_JS_LOGIN_3).read()

USER = 'user@mail.com'
PASS = 'passw0rd'


class BasicLoginRequestHandler(ExtendedHttpRequestHandler):
    LOGIN_FORM = VANILLA_JS_LOGIN_1
    ADMIN_HOME = u'Hello admin!'

    EVENTS = []

    @classmethod
    def clear_events(cls):
        cls.EVENTS = []

    def do_GET(self):
        #
        # This code is the HTTP request "router"
        #
        request_path = urlparse(self.path).path
        self.EVENTS.append(request_path)

        if request_path == '/login_form.py':
            return self.show_login()

        elif request_path == '/login_post.py':
            return self.do_login()

        elif request_path == '/admin':
            return self.show_admin()

        else:
            self.quick_response('Not found!', 404)

    def show_login(self):
        return self.quick_response(self.LOGIN_FORM)

    def show_admin(self):
        #
        # Check the session cookie and set admin_request_success for unittest
        #
        cookie = self.headers.get('Cookie', '')

        if not cookie:
            return self.quick_response('Forbidden', 403)

        if 'naming_is_hard' not in cookie:
            return self.quick_response('Forbidden', 403)

        self.EVENTS.append('ADMIN_REQUEST_SUCCESS')

        return self.quick_response(self.ADMIN_HOME)

    def do_login(self):
        #
        # Check username and password
        #
        query_string = urlparse(self.path).query
        query_string = parse_qs(query_string)

        request_user = query_string.get('username')[0]
        request_pass = query_string.get('password')[0]

        if request_user != USER:
            return self.quick_response('Invalid user', 403)

        if request_pass != PASS:
            return self.quick_response('Invalid password', 403)

        #
        # Build the response
        #
        headers = dict()
        headers['Set-Cookie'] = 'session=naming_is_hard'
        headers['Location'] = '/admin'
        headers['status'] = 302

        return self.send_response_to_client(302, 'Success', headers)


@pytest.mark.deprecated
class TestVanillaJavaScript1(PluginTest):

    SERVER_HOST = '127.0.0.1'
    SERVER_ROOT_PATH = '/tmp/'

    def start_webserver(self, request_handler_klass=BasicLoginRequestHandler):
        t, s, p = start_webserver_any_free_port(self.SERVER_HOST,
                                                webroot=self.SERVER_ROOT_PATH,
                                                handler=request_handler_klass)

        self.server_thread = t
        self.server = s
        self.server_port = p

        url = 'http://%s:%s/' % (self.SERVER_HOST, self.server_port)
        return URL(url)

    def tearDown(self):
        if self.server is not None:
            self.server.shutdown()

        if self.server_thread is not None:
            self.server_thread.join()

        BasicLoginRequestHandler.clear_events()

    def test_js_auth(self):
        target_url = self.start_webserver(BasicLoginRequestHandler)

        login_form_url = URL(target_url + 'login_form.py')
        check_url = URL(target_url + 'admin')
        check_string = BasicLoginRequestHandler.ADMIN_HOME

        plugins = {
            'audit': (PluginConfig('xss'),),
            'auth': (PluginConfig('autocomplete_js',
                                  ('username', USER, PluginConfig.STR),
                                  ('password', PASS, PluginConfig.STR),
                                  ('login_form_url', login_form_url, PluginConfig.URL),
                                  ('check_url', check_url, PluginConfig.URL),
                                  ('check_string', check_string, PluginConfig.STR)),),
        }

        self._scan(target_url.url_string, plugins)

        self.assertIn('/login_form.py', BasicLoginRequestHandler.EVENTS)
        self.assertIn('/login_post.py', BasicLoginRequestHandler.EVENTS)
        self.assertIn('/admin', BasicLoginRequestHandler.EVENTS)
        self.assertIn('ADMIN_REQUEST_SUCCESS', BasicLoginRequestHandler.EVENTS)


class FakeFormLoginRequestHandler(BasicLoginRequestHandler):
    LOGIN_FORM = VANILLA_JS_LOGIN_2


class TestVanillaJavaScript2(TestVanillaJavaScript1):

    def test_js_auth(self):
        target_url = self.start_webserver(FakeFormLoginRequestHandler)

        login_form_url = URL(target_url + 'login_form.py')
        check_url = URL(target_url + 'admin')
        check_string = FakeFormLoginRequestHandler.ADMIN_HOME

        plugins = {
            'audit': (PluginConfig('xss'),),
            'auth': (PluginConfig('autocomplete_js',
                                  ('username', USER, PluginConfig.STR),
                                  ('password', PASS, PluginConfig.STR),
                                  ('login_form_url', login_form_url, PluginConfig.URL),
                                  ('check_url', check_url, PluginConfig.URL),
                                  ('check_string', check_string, PluginConfig.STR)),),
        }

        self._scan(target_url.url_string, plugins)

        self.assertIn('/login_form.py', FakeFormLoginRequestHandler.EVENTS)
        self.assertIn('/login_post.py', FakeFormLoginRequestHandler.EVENTS)
        self.assertIn('/admin', FakeFormLoginRequestHandler.EVENTS)
        self.assertIn('ADMIN_REQUEST_SUCCESS', FakeFormLoginRequestHandler.EVENTS)


class NoEnterInInputsLoginRequestHandler(BasicLoginRequestHandler):
    LOGIN_FORM = VANILLA_JS_LOGIN_3


class TestVanillaJavaScript3(TestVanillaJavaScript1):

    def test_js_auth(self):
        target_url = self.start_webserver(NoEnterInInputsLoginRequestHandler)

        login_form_url = URL(target_url + 'login_form.py')
        check_url = URL(target_url + 'admin')
        check_string = FakeFormLoginRequestHandler.ADMIN_HOME

        plugins = {
            'audit': (PluginConfig('xss'),),
            'auth': (PluginConfig('autocomplete_js',
                                  ('username', USER, PluginConfig.STR),
                                  ('password', PASS, PluginConfig.STR),
                                  ('login_form_url', login_form_url, PluginConfig.URL),
                                  ('check_url', check_url, PluginConfig.URL),
                                  ('check_string', check_string, PluginConfig.STR)),),
        }

        self._scan(target_url.url_string, plugins)

        self.assertIn('/login_form.py', FakeFormLoginRequestHandler.EVENTS)
        self.assertIn('/login_post.py', FakeFormLoginRequestHandler.EVENTS)
        self.assertIn('/admin', FakeFormLoginRequestHandler.EVENTS)
        self.assertIn('ADMIN_REQUEST_SUCCESS', FakeFormLoginRequestHandler.EVENTS)


def test_autocomplete_js_reports_if_it_fails_to_use_css_selectors(
        plugin_runner,
        knowledge_base,
):
    autocomplete_js_config = {
        'username': 'test@example.com',
        'password': 'pass',
        'check_url': 'http://example.com/me/',
        'login_form_url': 'http://example.com/login/',
        'check_string': 'logged as',
        'username_field_css_selector': '#username',
        'login_button_css_selector': '#login',
        'login_form_activator_css_selector': '#activator',
    }
    autocomplete_js_plugin = autocomplete_js()
    plugin_runner.run_plugin(autocomplete_js_plugin, autocomplete_js_config)
    kb_result = knowledge_base.dump()
    errors = kb_result.get('authentication').get('error')
    css_error_count = 0
    for error in errors:
        if 'CSS selectors failed' in error.get_name():
            css_error_count += 1
    assert css_error_count


def test_autocomplete_js_doesnt_report_if_it_can_find_css_selectors(
        plugin_runner,
        knowledge_base,
        js_domain_with_login_form,
):
    autocomplete_js_config = {
        'username': 'test@example.com',
        'password': 'pass',
        'check_url': 'http://example.com/me/',
        'login_form_url': 'http://example.com/login/',
        'check_string': 'logged as',
        'username_field_css_selector': '#username',
        'login_button_css_selector': '#login',
    }
    autocomplete_js_plugin = autocomplete_js()
    for _ in range(1):
        plugin_runner.run_plugin(
            autocomplete_js_plugin,
            autocomplete_js_config,
            mock_domain=js_domain_with_login_form,
            do_end_call=False,
        )
    plugin_runner.plugin_last_ran.end()
    kb_result = knowledge_base.dump()
    assert not kb_result.get('authentication', {}).get('error')
