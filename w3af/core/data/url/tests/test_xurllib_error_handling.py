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
from w3af.core.controllers.exceptions import ScanMustStopByKnownReasonExc
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.data.url.tests.helpers.upper_daemon import ThreadingUpperDaemon
from w3af.core.data.constants.file_patterns import FILE_PATTERNS
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.url.tests.helpers.upper_daemon import UpperDaemon
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.tests.test_xurllib import (EmptyTCPHandler,
                                                   TimeoutTCPHandler)


TIMEOUT_SECS = 1


@attr('moth')
@attr('smoke')
class TestXUrllibDelayOnError(unittest.TestCase):

    def setUp(self):
        self.uri_opener = ExtendedUrllib()

    def tearDown(self):
        self.uri_opener.end()

    def test_increasing_delay_on_errors(self):
        expected_log = {0: False, 70: False, 40: False, 10: False, 80: False,
                        50: False, 20: False, 90: False, 60: False, 30: False,
                        100: False}
        self.assertEqual(self.uri_opener._sleep_log, expected_log)

        return_empty_daemon = UpperDaemon(EmptyTCPHandler)
        return_empty_daemon.start()
        return_empty_daemon.wait_for_start()

        port = return_empty_daemon.get_port()

        # No retries means that the test is easier to read/understand
        self.uri_opener.settings.set_max_http_retries(0)

        # We want to keep going, don't test the _should_stop_scan here.
        self.uri_opener._should_stop_scan = lambda x: False
        self.uri_opener._rate_limit = lambda: True

        url = URL('http://127.0.0.1:%s/' % port)
        http_exception_count = 0
        loops = 100

        # Now check the delays
        with patch('w3af.core.data.url.extended_urllib.time.sleep') as sleepm:
            for i in xrange(loops):
                try:
                    self.uri_opener.GET(url, cache=False)
                except HTTPRequestException:
                    http_exception_count += 1
                except Exception, e:
                    msg = 'Not expecting: "%s"'
                    self.assertTrue(False, msg % e.__class__.__name__)
                else:
                    self.assertTrue(False, 'Expecting HTTPRequestException')

            self.assertEqual(loops - 1, i)

            # Note that the timeouts are increasing based on the error rate and
            # SOCKET_ERROR_DELAY
            expected_calls = [call(1.5),
                              call(3.0),
                              call(4.5),
                              call(6.0),
                              call(7.5),
                              call(9.0),
                              call(10.5),
                              call(12.0),
                              call(13.5)]

            expected_log = {0: False, 70: True, 40: True, 10: True, 80: True,
                            50: True, 20: True, 90: True, 60: True, 30: True,
                            100: False}
            self.assertEqual(expected_calls, sleepm.call_args_list)
            self.assertEqual(http_exception_count, 100)
            self.assertEqual(self.uri_opener._sleep_log, expected_log)

            # This one should also clear the log
            try:
                self.uri_opener.GET(url, cache=False)
            except HTTPRequestException:
                pass
            else:
                self.assertTrue(False, 'Expected HTTPRequestException')

            # The log was cleared, all values should be False
            self.assertTrue(all([not v for v in self.uri_opener._sleep_log.values()]))

    def test_error_handling_disable_per_request(self):
        upper_daemon = UpperDaemon(TimeoutTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()

        self.uri_opener.settings.set_configured_timeout(1)
        self.uri_opener.clear_timeout()
        self.uri_opener._retry = Mock()

        url = URL('http://127.0.0.1:%s/' % port)

        try:
            self.uri_opener.GET(url, error_handling=False)
        except HTTPRequestException:
            self.assertEqual(self.uri_opener._retry.call_count, 0)
        else:
            self.assertTrue(False, 'Exception not raised')

        self.uri_opener.settings.set_default_values()

    def test_exception_is_raised_always_after_stop(self):
        return_empty_daemon = UpperDaemon(EmptyTCPHandler)
        return_empty_daemon.start()
        return_empty_daemon.wait_for_start()

        port = return_empty_daemon.get_port()

        # No retries means that the test is easier to read/understand
        self.uri_opener.settings.set_max_http_retries(0)

        # Don't rate limit
        self.uri_opener._rate_limit = lambda: True

        url = URL('http://127.0.0.1:%s/' % port)
        http_exception_count = 0
        loops = 100

        # Loop until we reach a must stop exception
        for i in xrange(loops):
            try:
                self.uri_opener.GET(url, cache=False)
            except HTTPRequestException:
                http_exception_count += 1
            except ScanMustStopByKnownReasonExc, smse:
                break
            except Exception, e:
                msg = 'Not expecting: "%s"'
                self.assertTrue(False, msg % e.__class__.__name__)
            else:
                self.assertTrue(False, 'Expecting an exception')

        # We quickly reach this state, which is good since the server is down
        self.assertEquals(http_exception_count, 9)

        # After reaching this state we will always yield ScanMustStopByKnownReasonExc
        for i in xrange(loops):
            self.assertRaises(ScanMustStopByKnownReasonExc,
                              self.uri_opener.GET, url, cache=False)

        # Confirm that this is the code section raising the exception
        self.uri_opener._raise_if_should_stop = lambda: True
        self.assertRaises(HTTPRequestException, self.uri_opener.GET, url, cache=False)


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
        self.w3afcore.uri_opener.clear_timeout()

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

            # This assertion does fail often due to threads sending stuff in
            # "different order"
            #msg = 'Remote URL %s is reachable'
            #self.assertIn(call.debug(msg % target_url), om_mock.mock_calls)

            # This one should appear each time
            msg = 'ExtendedUrllib error rate is at 10%'
            self.assertIn(call.debug(msg), om_mock.mock_calls)

            self.assertEqual(om_mock.report_finding.call_count, 1)

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
