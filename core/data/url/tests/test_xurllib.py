# -*- coding: utf-8 -*-
'''
test_xurllib.py

Copyright 2011 Andres Riancho

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
'''
import os
import time
import unittest
import Queue
import SocketServer

from multiprocessing.dummy import Process
from nose.plugins.attrib import attr

from core.data.url.extended_urllib import ExtendedUrllib, MAX_ERROR_COUNT
from core.data.url.tests.helpers.upper_daemon import UpperDaemon
from core.data.parsers.url import URL
from core.data.dc.data_container import DataContainer
from core.data.dc.headers import Headers

from core.controllers.misc.temp_dir import get_temp_dir
from core.controllers.exceptions import (w3afMustStopByUserRequest,
                                         w3afMustStopOnUrlError,
                                         w3afMustStopException,
                                         w3afMustStopByUnknownReasonExc)


@attr('moth')
@attr('smoke')
class TestXUrllib(unittest.TestCase):

    MOTH_MESSAGE = 'Welcome to the moth homepage!'

    def setUp(self):
        self.uri_opener = ExtendedUrllib()
    
    def tearDown(self):
        self.uri_opener.end()
        
    def test_basic(self):
        url = URL('http://moth/')
        http_response = self.uri_opener.GET(url, cache=False)
        
        self.assertIn(self.MOTH_MESSAGE, http_response.body)
        
        self.assertGreaterEqual(http_response.id, 1)
        self.assertNotEqual(http_response.id, None)

    def test_cache(self):
        url = URL('http://moth/')
        http_response = self.uri_opener.GET(url)
        self.assertTrue(self.MOTH_MESSAGE in http_response.body)

        url = URL('http://moth/')
        http_response = self.uri_opener.GET(url)
        self.assertTrue(self.MOTH_MESSAGE in http_response.body)

    def test_qs_params(self):
        url = URL('http://moth/w3af/audit/local_file_read/local_file_read.php?file=section.txt')
        http_response = self.uri_opener.GET(url, cache=False)
        self.assertTrue('Showing the section content.' in http_response.body,
                        http_response.body)

        url = URL('http://moth/w3af/audit/local_file_read/local_file_read.php?file=/etc/passwd')
        http_response = self.uri_opener.GET(url, cache=False)
        self.assertTrue(
            'root:x:0:0:' in http_response.body, http_response.body)

    def test_POST(self):
        url = URL('http://moth/w3af/audit/xss/data_receptor2.php')
        data = DataContainer([('empresa', 'abc'), ('firstname', 'def')])
        http_response = self.uri_opener.POST(url, data, cache=False)
        self.assertTrue('def' in http_response.body, http_response.body)

    def test_POST_special_chars(self):
        url = URL('http://moth/w3af/audit/xss/data_receptor2.php')
        test_data = u'abc<def>"-á-'
        data = DataContainer([('empresa', test_data), ('firstname', 'def')])
        http_response = self.uri_opener.POST(url, data, cache=False)
        self.assertIn(test_data, http_response.body)

    def test_unknown_url(self):
        url = URL('http://longsitethatdoesnotexistfoo.com/')
        self.assertRaises(w3afMustStopOnUrlError, self.uri_opener.GET, url)

    def test_url_port_closed(self):
        # TODO: Change 2312 by an always closed/non-http port
        url = URL('http://127.0.0.1:2312/')
        self.assertRaises(w3afMustStopOnUrlError, self.uri_opener.GET, url)

    def test_url_port_not_http(self):
        upper_daemon = UpperDaemon(EmptyTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()

        url = URL('http://127.0.0.1:%s/' % port)
        self.assertRaises(w3afMustStopOnUrlError, self.uri_opener.GET, url)

    def test_url_port_not_http_many(self):
        upper_daemon = UpperDaemon(EmptyTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()

        url = URL('http://127.0.0.1:%s/' % port)
        for _ in xrange(MAX_ERROR_COUNT):
            try:
                self.uri_opener.GET(url)
            except w3afMustStopByUnknownReasonExc:
                self.assertTrue(False, 'Not expecting this exception type.')
            except w3afMustStopOnUrlError:
                self.assertTrue(True)
            except w3afMustStopException:
                self.assertTrue(True)
                break
        else:
            self.assertTrue(False)

    def test_timeout(self):
        upper_daemon = UpperDaemon(TimeoutTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()
        
        url = URL('http://127.0.0.1:%s/' % port)
        
        self.uri_opener.settings.set_timeout(1)
        
        self.assertRaises(w3afMustStopOnUrlError, self.uri_opener.GET, url)
        
        self.uri_opener.settings.set_default_values()

    def test_timeout_many(self):
        upper_daemon = UpperDaemon(TimeoutTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()

        self.uri_opener.settings.set_timeout(1)

        url = URL('http://127.0.0.1:%s/' % port)
        
        for _ in xrange(MAX_ERROR_COUNT):
            try:
                self.uri_opener.GET(url)
            except w3afMustStopByUnknownReasonExc:
                self.assertTrue(False, 'Not expecting this exception type.')
            except w3afMustStopOnUrlError:
                self.assertTrue(True)
            except w3afMustStopException, e:
                self.assertTrue(True)
                break
        else:
            self.assertTrue(False)
        
        self.uri_opener.settings.set_default_values()
        
    def test_stop(self):
        self.uri_opener.stop()
        url = URL('http://moth/')
        self.assertRaises(w3afMustStopByUserRequest, self.uri_opener.GET, url)

    def test_pause_stop(self):
        self.uri_opener.pause(True)
        self.uri_opener.stop()
        url = URL('http://moth/')
        self.assertRaises(w3afMustStopByUserRequest, self.uri_opener.GET, url)

    def test_pause(self):
        output = Queue.Queue()
        self.uri_opener.pause(True)

        def send(uri_opener, output):
            url = URL('http://moth/')
            http_response = uri_opener.GET(url)
            output.put(http_response)

        th = Process(target=send, args=(self.uri_opener, output))
        th.daemon = True
        th.start()

        self.assertRaises(Queue.Empty, output.get, True, 2)

    def test_pause_unpause(self):
        output = Queue.Queue()
        self.uri_opener.pause(True)

        def send(uri_opener, output):
            url = URL('http://moth/')
            http_response = uri_opener.GET(url)
            output.put(http_response)

        th = Process(target=send, args=(self.uri_opener, output))
        th.daemon = True
        th.start()

        self.assertRaises(Queue.Empty, output.get, True, 2)

        self.uri_opener.pause(False)

        http_response = output.get()
        th.join()
        
        self.assertEqual(http_response.get_code(), 200)
        self.assertIn(self.MOTH_MESSAGE, http_response.body)
    
    def test_removes_cache(self):
        url = URL('http://moth/')
        self.uri_opener.GET(url, cache=False)
        
        # Please note that this line, together with the tearDown() act as
        # a test for a "double call to end()".
        self.uri_opener.end()
        
        db_fmt = 'db_unittest-%s'
        trace_fmt = 'db_unittest-%s_traces/'
        temp_dir = get_temp_dir()
        
        for i in xrange(100):
            test_db_path = os.path.join(temp_dir, db_fmt % i)
            test_trace_path = os.path.join(temp_dir, trace_fmt % i)
            self.assertFalse(os.path.exists(test_db_path), test_db_path)
            self.assertFalse(os.path.exists(test_trace_path), test_trace_path)
    
    def test_special_char_header(self):
        url = URL('http://moth/w3af/core/header_fuzzing/cookie_echo.php')
        header_content = u'á'
        headers = Headers([('foo', header_content)])
        http_response = self.uri_opener.GET(url, cache=False, headers=headers)
        self.assertEqual(header_content, http_response.body)

class EmptyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        self.request.sendall('')

class TimeoutTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        time.sleep(60)
        self.request.sendall('')