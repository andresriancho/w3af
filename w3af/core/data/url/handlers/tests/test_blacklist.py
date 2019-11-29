"""
test_blacklist.py

Copyright 2013 Andres Riancho

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
import re
import unittest
import urllib2
import httpretty

import w3af.core.data.kb.config as cf

from w3af.core.controllers.misc.number_generator import consecutive_number_generator
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.constants.response_codes import NO_CONTENT
from w3af.core.data.url.handlers.blacklist import BlacklistHandler
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url import opener_settings


class TestBlacklistHandler(unittest.TestCase):

    MOCK_URL = 'http://w3af.org/scanner/'
    MOCK_URL_BLOCK = 'http://w3af.org/block/'
    MOCK_URL_PASS = 'http://w3af.org/pass/'
    MOCK_BODY = 'Hello world'
    
    def setUp(self):
        consecutive_number_generator.reset()
        cf.cf.save('blacklist_http_request', [])
        cf.cf.save('ignore_regex', None)

    def tearDown(self):
        cf.cf.save('blacklist_http_request', [])
        cf.cf.save('ignore_regex', None)

    @httpretty.activate
    def test_blacklist_handler_block(self):
        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL,
                               body=self.MOCK_BODY,
                               status=200)

        # Configure the handler
        blocked_url = URL(self.MOCK_URL)
        cf.cf.save('blacklist_http_request', [blocked_url])
        
        opener = urllib2.build_opener(BlacklistHandler)
        
        request = urllib2.Request(blocked_url.url_string)
        request.url_object = blocked_url
        response = opener.open(request)
        
        self.assertEqual(response.code, NO_CONTENT)
        self.assertIsInstance(httpretty.last_request(), httpretty.core.HTTPrettyRequestEmpty)
    
    @httpretty.activate
    def test_blacklist_handler_pass(self):
        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL,
                               body=self.MOCK_BODY,
                               status=200)

        opener = urllib2.build_opener(BlacklistHandler)
        
        request = urllib2.Request(self.MOCK_URL)
        request.url_object = URL(self.MOCK_URL)
        response = opener.open(request)
        
        self.assertEqual(response.code, 200)
        self.assertEqual(httpretty.last_request().method, httpretty.GET)

    @httpretty.activate
    def test_handler_order_block(self):
        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL,
                               body=self.MOCK_BODY,
                               status=200)

        blocked_url = URL(self.MOCK_URL)
        cf.cf.save('blacklist_http_request', [blocked_url])

        # Get an instance of the extended urllib and verify that the blacklist
        # handler still works, even when mixed with all the other handlers.
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(blocked_url)
        response = opener.open(request)
        
        self.assertEqual(response.code, NO_CONTENT)
        self.assertEqual(response.id, 1)
        self.assertIsInstance(httpretty.last_request(), httpretty.core.HTTPrettyRequestEmpty)
        
    @httpretty.activate
    def test_handler_order_pass(self):
        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL_BLOCK,
                               body=self.MOCK_BODY,
                               status=200)

        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL_PASS,
                               body=self.MOCK_BODY,
                               status=200)

        blocked_url = URL(self.MOCK_URL_BLOCK)
        safe_url = URL(self.MOCK_URL_PASS)
        cf.cf.save('blacklist_http_request', [blocked_url])

        # Get an instance of the extended urllib and verify that the blacklist
        # handler still works, even when mixed with all the other handlers.
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(safe_url)
        response = opener.open(request)

        last_request = httpretty.last_request()

        self.assertEqual(response.code, 200)
        self.assertEqual(response.id, 1)
        self.assertEqual(last_request.method, httpretty.GET)

        request = HTTPRequest(blocked_url)
        response = opener.open(request)

        self.assertEqual(response.code, 204)
        self.assertEqual(response.id, 2)
        self.assertIs(last_request, httpretty.last_request())

    @httpretty.activate
    def test_handler_order_pass_with_ignore_regex(self):
        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL_BLOCK,
                               body=self.MOCK_BODY,
                               status=200)

        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL_PASS,
                               body=self.MOCK_BODY,
                               status=200)

        blocked_url = URL(self.MOCK_URL_BLOCK)
        safe_url = URL(self.MOCK_URL_PASS)

        ignore_regex = re.compile('.*block.*')
        cf.cf.save('ignore_regex', ignore_regex)

        # Get an instance of the extended urllib and verify that the blacklist
        # handler still works, even when mixed with all the other handlers.
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(safe_url)
        response = opener.open(request)

        last_request = httpretty.last_request()

        self.assertEqual(response.code, 200)
        self.assertEqual(response.id, 1)

        request = HTTPRequest(blocked_url)
        response = opener.open(request)

        self.assertEqual(response.code, 204)
        self.assertEqual(response.id, 2)
        self.assertIs(last_request, httpretty.last_request())

    @httpretty.activate
    def test_handler_order_pass_with_both_methods(self):
        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL_BLOCK,
                               body=self.MOCK_BODY,
                               status=200)

        httpretty.register_uri(httpretty.GET,
                               self.MOCK_URL_PASS,
                               body=self.MOCK_BODY,
                               status=200)

        blocked_url = URL(self.MOCK_URL_BLOCK)
        safe_url = URL(self.MOCK_URL_PASS)

        cf.cf.save('blacklist_http_request', [blocked_url])

        ignore_regex = re.compile('.*blo.*')
        cf.cf.save('ignore_regex', ignore_regex)

        # Get an instance of the extended urllib and verify that the blacklist
        # handler still works, even when mixed with all the other handlers.
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(safe_url)
        response = opener.open(request)

        last_request = httpretty.last_request()

        self.assertEqual(response.code, 200)
        self.assertEqual(response.id, 1)

        request = HTTPRequest(blocked_url)
        response = opener.open(request)

        self.assertEqual(response.code, 204)
        self.assertEqual(response.id, 2)
        self.assertIs(last_request, httpretty.last_request())
