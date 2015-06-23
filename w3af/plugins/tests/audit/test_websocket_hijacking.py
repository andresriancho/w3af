"""
test_websocket_hijacking.py

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
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info import Info
from w3af.plugins.grep.websockets_links import WebSocketInfoSet
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


RUN_CONFIG = {
    'cfg': {
        'target': None,
        'plugins': {
            'audit': (PluginConfig('websocket_hijacking'),),
        }
    }
}

ALL_RUN_CONFIG = {
    'cfg': {
        'target': None,
        'plugins': {
            'audit': (PluginConfig('websocket_hijacking'),),
            'grep': (PluginConfig('websockets_links'),),
            'crawl': (PluginConfig('web_spider'),),
        }
    }
}

SUCCESSFUL_UPGRADE = {'Upgrade': 'websocket',
                      'Connection': 'Upgrade',
                      'Sec-WebSocket-Accept': 'HSmrc0sMlYUkAGmm5OPpG2HaGWk=',
                      'Sec-WebSocket-Protocol': 'chat'}


class WebSocketTest(PluginTest):

    def verify_found(self, vulnerability_names):
        """
        Runs the scan and verifies that the vulnerability with the specified
        name was found.

        :param vulnerability_names: The names of the vulnerabilities to be found
        :return: None. Will raise assertion if fails
        """
        # Setup requirements
        desc = 'The URL: "%s" uses HTML5 websocket "%s"'
        desc %= (self.target_url, self.target_url)

        i = Info('HTML5 WebSocket detected', desc, 1, 'websockets_links')
        i.set_url(URL(self.target_url))
        i[WebSocketInfoSet.ITAG] = self.target_url

        # Store found links
        info_set = WebSocketInfoSet([i])
        self.kb.append('websockets_links', 'websockets_links', i, info_set)

        # Run the plugin
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])

        # Assert
        vulns = self.kb.get('websocket_hijacking', 'websocket_hijacking')
        self.assertEqual(vulnerability_names, [v.get_name() for v in vulns])


class OpenWebSocketsTest(WebSocketTest):

    target_url = 'http://websocket.com/service'
    target_ws = 'ws://websocket.com/service'

    MOCK_RESPONSES = [MockResponse(url=target_url,
                                   body='',
                                   method='GET',
                                   status=101,
                                   headers=SUCCESSFUL_UPGRADE)]

    def test_open_websockets(self):
        self.verify_found(['Open WebSocket'])


class NoWebSocketTest(WebSocketTest):

    target_url = 'http://websocket.com/service'
    target_ws = 'ws://websocket.com/service'

    MOCK_RESPONSES = [MockResponse(url=target_url,
                                   body='Hi there',
                                   method='GET',
                                   status=200)]

    def test_no_websockets(self):
        self.verify_found([])


class OriginMatchBugTest(WebSocketTest):

    target_url = 'http://websocket.com'
    target_ws = 'ws://websocket.com'

    class OriginMatchBugMock(MockResponse):
        def matches(self, http_request, uri, response_headers):
            origin = http_request.headers.get('origin', '')
            if origin.startswith(OriginMatchBugTest.target_url):
                return True

            return False

    MOCK_RESPONSES = [OriginMatchBugMock(url=target_url,
                                         body='',
                                         method='GET',
                                         status=101,
                                         headers=SUCCESSFUL_UPGRADE)]

    def test_origin_match_bug_websockets(self):
        self.verify_found(['Insecure WebSocket Origin filter'])


class OriginMatchTest(WebSocketTest):

    target_url = 'http://websocket.com'
    target_ws = 'ws://websocket.com'

    class OriginMatchMock(MockResponse):
        def matches(self, http_request, uri, response_headers):
            origin = http_request.headers.get('origin', '')
            if origin == OriginMatchBugTest.target_url:
                return True

            return False

    MOCK_RESPONSES = [OriginMatchMock(url=target_url,
                                      body='',
                                      method='GET',
                                      status=101,
                                      headers=SUCCESSFUL_UPGRADE)]

    def test_origin_match_test_websockets(self):
        self.verify_found(['Origin restricted WebSocket'])


class BasicAuthWebSocketTest(WebSocketTest):

    target_url = 'http://websocket.com'
    target_ws = 'ws://websocket.com'

    class BasicAuthMock(MockResponse):
        def matches(self, http_request, uri, response_headers):
            authorization = http_request.headers.get('authorization', '')
            if authorization:
                return True

            return False

    MOCK_RESPONSES = [BasicAuthMock(url=target_url,
                                    body='',
                                    method='GET',
                                    status=101,
                                    headers=SUCCESSFUL_UPGRADE)]

    def setup_basic_authentication(self):
        self.w3afcore.uri_opener.settings.set_basic_auth(URL('websocket.com'),
                                                         'user1', 'password')

    def test_basic_auth_websockets(self):
        self.setup_basic_authentication()
        self.verify_found(['Websockets CSRF vulnerability'])


class CookieAuthWebSocketTest(WebSocketTest):

    target_url = 'http://websocket.com'
    target_ws = 'ws://websocket.com'

    class CookieAuthMock(MockResponse):
        def get_response(self, http_request, uri, response_headers):
            origin = http_request.headers.get('origin', '')
            cookie = http_request.headers.get('cookie', '')
            if origin and cookie == 'foo=123':
                response_headers.update(SUCCESSFUL_UPGRADE)
                return 101, response_headers, ''
            else:
                response_headers.update({'Set-Cookie': 'foo=123'})
                return 200, response_headers, 'Cookies sent'

        def matches(self, http_request, uri, response_headers):
            return True

    MOCK_RESPONSES = [CookieAuthMock(url=target_url,
                                     body=None,
                                     method='GET',
                                     status=None)]

    def test_cookie_auth_websockets(self):
        self.verify_found(['Websockets CSRF vulnerability'])


class OpenWebSocketsWithCrawlTest(WebSocketTest):
    """
    Test that we can grep a page, extract WS links, and then audit them in
    the audit plugin.
    """
    target_url = 'http://w3af.com/'

    target_ws_http = 'http://w3af.com/echo'
    target_ws = 'ws://w3af.com/echo'

    INDEX_BODY = ('<html>'
                  '<a href="/ws-index">ws index</a>'
                  '</html>')

    WS_BODY = ('<html>'
               '<script>'
               'var connection = new WebSocket("ws://w3af.com/echo");'
               '</script>'
               '</html>')

    MOCK_RESPONSES = [MockResponse(url=target_url,
                                   body=INDEX_BODY,
                                   method='GET',
                                   status=200),
                      MockResponse(url=target_url + 'ws-index',
                                   body=WS_BODY,
                                   method='GET',
                                   status=200),
                      MockResponse(url=target_ws_http,
                                   body='',
                                   method='GET',
                                   status=101,
                                   headers=SUCCESSFUL_UPGRADE)]

    def test_open_websockets_with_crawl(self):
        # Run the plugin
        cfg = ALL_RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])

        # Assert
        vulns = self.kb.get('websocket_hijacking', 'websocket_hijacking')
        self.assertEqual(['Open WebSocket'], [v.get_name() for v in vulns])