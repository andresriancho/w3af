"""
test_find_vhosts.py

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
import SocketServer

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.core.data.url.tests.helpers.upper_daemon import ThreadingUpperDaemon


class TestFindVhosts(PluginTest):
    #
    # Note: I tried implementing this test using httpretty and found
    #       that it doesn't support the connection to w3af.org with
    #       a Host header that specifies a different host.
    #
    #       That is why we need a real server for testing.
    #
    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('find_vhosts'),)}
        }
    }

    def test_find_vhosts(self):
        # Setup the server
        upper_daemon = ThreadingUpperDaemon(MultipleVHostsHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()
        target_url = 'http://127.0.0.1:%s/' % port

        cfg = self._run_configs['cfg']
        self._scan(target_url, cfg['plugins'])

        infos = self.kb.get('find_vhosts', 'find_vhosts')
        self.assertEqual(len(infos), 1, infos)

        info = infos[0]
        self.assertEqual('Virtual host identified', info.get_name())
        self.assertTrue('the virtual host name is: "intranet"' in info.get_desc(), info.get_desc())


class TestFindVhostsInHTML(PluginTest):
    target_url = 'http://w3af.org'

    MOCK_RESPONSES = [MockResponse(target_url, '<a href="http://intranet/">x</a>')]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('find_vhosts'),)}
        }
    }

    def test_find_vhost_dead_link(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_url, cfg['plugins'])

        infos = self.kb.get('find_vhosts', 'find_vhosts')
        self.assertEqual(len(infos), 1, infos)

        expected = {'Internal hostname in HTML link'}
        self.assertEqual(expected, {i.get_name() for i in infos})


class MultipleVHostsHandler(SocketServer.BaseRequestHandler):
    RESPONSE = ('HTTP/1.0 200 Ok\r\n'
                'Connection: Close\r\n'
                'Content-Length: %s\r\n'
                'Content-Type: text/html\r\n'
                '\r\n%s')

    RESPONSE_404 = ('HTTP/1.0 404 Not Found\r\n'
                    'Connection: Close\r\n'
                    'Content-Length: %s\r\n'
                    'Content-Type: text/html\r\n'
                    '\r\n%s')

    def handle(self):
        data = self.request.recv(1024).strip()

        # Match hosts
        if 'Host: w3af.org\r\n' in data:
            body = 'Welcome to w3af.org'
            self.request.sendall(self.RESPONSE % (len(body), body))

        if 'Host: intranet\r\n' in data:
            body = 'Intranet secrets are here'
            self.request.sendall(self.RESPONSE % (len(body), body))

        else:
            body = 'Not found'
            self.request.sendall(self.RESPONSE_404 % (len(body), body))
