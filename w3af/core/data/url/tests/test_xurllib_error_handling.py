# -*- coding: utf-8 -*-
"""
test_xurllib_error_handling.py

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
import time
import SocketServer

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.url.tests.helpers.upper_daemon import UpperDaemon

TIMEOUT_SECS = 1


class TestXUrllibErrorHandling(PluginTest):
    """
    We test that our xurllib can handle the case found at #8698 where many
    threads were sending requests to a URL which was timing out, thus reaching
    the MAX_ERROR_COUNT and stopping the whole scan.

    :see: https://github.com/andresriancho/w3af/issues/8698#issuecomment-77625343
    :see: https://github.com/andresriancho/w3af/issues/8698
    """
    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                'audit': (PluginConfig('lfi'),),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_do_not_reach_must_stop_exception(self):
        # Configure low timeout to have faster test
        self.w3afcore.uri_opener.settings.set_timeout(TIMEOUT_SECS)

        # Setup the server
        upper_daemon = UpperDaemon(MultipleTimeoutsTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()
        target_url = 'http://127.0.0.1:%s/' % port

        # Make sure we don't clear the attribute we want to assert
        self.w3afcore.uri_opener.clear = lambda: None

        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(target_url, cfg['plugins'], debug=True)

        # Restore the defaults
        self.w3afcore.uri_opener.settings.set_default_values()

        # No exceptions please
        self.assertIsNone(self.w3afcore.uri_opener._stop_exception)


class MultipleTimeoutsTCPHandler(SocketServer.BaseRequestHandler):
    RESPONSE = ('HTTP/1.0 200 Ok\r\n'
                'Connection: Close\r\n'
                'Content-Length: %s\r\n'
                'Content-Type: text/html\r\n'
                '\r\n%s')

    KA_RESPONSE = ('HTTP/1.0 200 Ok\r\n'
                   'Connection: Keep-Alive\r\n'
                   'Content-Length: %s\r\n'
                   'Content-Type: text/html\r\n'
                   '\r\n%s')

    RESPONSE_404 = ('HTTP/1.0 404 Not Found\r\n'
                    'Connection: Close\r\n'
                    'Content-Length: %s\r\n'
                    'Content-Type: text/html\r\n'
                    '\r\n%s')

    def handle(self):
        fake_file = self.request.makefile()
        header = fake_file.readline()

        # Note the space after the =, these requests are to get the original
        # response and shouldn't be delayed
        if '?f= ' in header:
            body = 'Empty parameter'
            self.request.sendall(self.RESPONSE % (len(body), body))

        # Handling of the delayed+keep-alive responses
        elif '?f=' in header:
            time.sleep(TIMEOUT_SECS * 3)
            body = 'Slow response'
            self.request.sendall(self.KA_RESPONSE % (len(body), body))

        elif ' / ' in header:
            # Handling the index
            links = ('<a href="/1?f=">1</a>'
                     '<a href="/2?f=">2</a>'
                     '<a href="/3?f=">3</a>'
                     '<a href="/4?f=">4</a>')
            self.request.sendall(self.RESPONSE % (len(links), links))
        else:
            body = 'Not found'
            self.request.sendall(self.RESPONSE_404 % (len(body), body))
