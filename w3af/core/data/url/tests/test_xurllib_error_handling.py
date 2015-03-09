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
import unittest
import SocketServer

from mock import Mock, patch, call
from nose.plugins.attrib import attr

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.url.tests.helpers.upper_daemon import ThreadingUpperDaemon
from w3af.core.data.url.tests.test_xurllib import (EmptyTCPHandler,
                                                   TimeoutTCPHandler)
from w3af.core.data.constants.file_patterns import FILE_PATTERNS
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.url.constants import MAX_ERROR_COUNT, SOCKET_ERROR_DELAY
from w3af.core.data.url.tests.helpers.upper_daemon import UpperDaemon
from w3af.core.data.parsers.url import URL
from w3af.core.controllers.exceptions import (HTTPRequestException,
                                              ScanMustStopException)

TIMEOUT_SECS = 1


@attr('moth')
@attr('smoke')
class TestXUrllibDelayOnError(unittest.TestCase):

    def setUp(self):
        self.uri_opener = ExtendedUrllib()

    def tearDown(self):
        self.uri_opener.end()

    def test_delay_on_errors(self):
        return_empty_daemon = UpperDaemon(EmptyTCPHandler)
        return_empty_daemon.start()
        return_empty_daemon.wait_for_start()

        port = return_empty_daemon.get_port()

        url = URL('http://127.0.0.1:%s/' % port)
        previous_time = 0.0
        total_time = 0.0

        # Not check the delays
        for i in xrange(MAX_ERROR_COUNT):
            start = time.time()
            try:
                self.uri_opener.GET(url, cache=False)
            except HTTPRequestException:
                self.assertTrue(True)
                end = time.time()

                self.assertGreater(end - start, previous_time)
                previous_time = end - start
                total_time += previous_time

            except ScanMustStopException:
                self.assertTrue(True)
                break
            except Exception, e:
                msg = 'Not expecting: "%s"'
                self.assertTrue(False, msg % e.__class__.__name__)
        else:
            self.assertTrue(False)

        expected_total_delay = 0.0
        for i in xrange(MAX_ERROR_COUNT):
            expected_total_delay += SOCKET_ERROR_DELAY * i

        self.assertGreater(expected_total_delay, total_time)

    def test_error_handling_disable(self):
        upper_daemon = UpperDaemon(TimeoutTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()

        self.uri_opener.settings.set_configured_timeout(1)
        self.uri_opener._retry = Mock()

        url = URL('http://127.0.0.1:%s/' % port)

        try:
            self.uri_opener.GET(url, error_handling=False)
        except HTTPRequestException:
            self.assertEqual(self.uri_opener._retry.call_count, 0)
        else:
            self.assertTrue(False, 'Exception not raised')

        self.uri_opener.settings.set_default_values()


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
        self.w3afcore.uri_opener.settings.set_configured_timeout(TIMEOUT_SECS)

        # Setup the server
        upper_daemon = ThreadingUpperDaemon(MultipleTimeoutsTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()
        target_url = 'http://127.0.0.1:%s/' % port

        # Make sure we don't clear the attribute we want to assert
        self.w3afcore.uri_opener.clear = Mock()

        # Run the scan
        cfg = self._run_configs['cfg']

        with patch('w3af.core.data.url.extended_urllib.om.out') as om_mock:
            self._scan(target_url, cfg['plugins'])

            self.assertIn(call.debug('Remote server is reachable'),
                          om_mock.mock_calls)

        # Restore the defaults
        self.w3afcore.uri_opener.settings.set_default_values()

        # No exceptions please
        self.assertIsNone(self.w3afcore.uri_opener._stop_exception)

        # Assert the vulnerability findings
        vulns = self.kb.get('lfi', 'lfi')

        # Verify the specifics about the vulnerabilities
        expected = [('5', 'g')]

        self.assertAllVulnNamesEqual('Local file inclusion vulnerability', vulns)
        self.assertExpectedVulnsFound(expected, vulns)
        self.assertTrue(self.w3afcore.uri_opener.clear.called)


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
        header = fake_file.readline().strip()

        # Note the space after the =, these requests are to get the original
        # response and shouldn't be delayed
        if '?f= ' in header or '?g= ' in header:
            body = 'Empty parameter'
            self.request.sendall(self.RESPONSE % (len(body), body))

        # Handling of the delayed+keep-alive responses
        elif '?f=' in header:
            time.sleep(TIMEOUT_SECS * 3)
            body = 'Slow response'
            self.request.sendall(self.KA_RESPONSE % (len(body), body))

        # Handling of the vulnerability mock
        elif 'etc%2Fpasswd' in header:
            body = 'Header %s Footer' % FILE_PATTERNS[0]
            self.request.sendall(self.RESPONSE % (len(body), body))

        elif ' / ' in header:
            # Handling the index
            links = ('<a href="/1?f=">1</a>'
                     #'<a href="/2?f=">2</a>'
                     #'<a href="/3?f=">3</a>'
                     #'<a href="/4?f=">4</a>'
                     '<a href="/5?g=">5</a>')
            self.request.sendall(self.RESPONSE % (len(links), links))
        else:
            body = 'Not found'
            self.request.sendall(self.RESPONSE_404 % (len(body), body))
