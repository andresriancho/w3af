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

from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.daemons.webserver import start_webserver_any_free_port
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.data.parsers.doc.url import URL

VANILLA_JS_LOGIN = os.path.join(ROOT_PATH, 'plugins/tests/auth/autocomplete_js/vanilla_javascript_1/index.html')
VANILLA_JS_LOGIN = file(VANILLA_JS_LOGIN).read()

USER = 'user@mail.com'
PASS = 'passw0rd'


class BasicLoginRequestHandler(ExtendedHttpRequestHandler):
    LOGIN_FORM = VANILLA_JS_LOGIN
    ADMIN_HOME = u'Hello admin!'

    EVENTS = []

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

        BasicLoginRequestHandler.EVENTS = []

    def test_find_form_submit_login_check(self):
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
