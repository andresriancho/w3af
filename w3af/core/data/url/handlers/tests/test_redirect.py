"""
test_redirect.py

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
import urllib2
import unittest
import httpretty

from w3af.core.controllers.misc.number_generator import consecutive_number_generator
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.constants.response_codes import FOUND, OK, MOVED_PERMANENTLY
from w3af.core.data.url.handlers.redirect import HTTP30XHandler
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url import opener_settings


class TestRedirectHandlerLowLevel(unittest.TestCase):

    REDIR_DEST = 'http://w3af.org/dest'
    REDIR_SRC = 'http://w3af.org/src'
    OK_BODY = 'Body!'

    def setUp(self):
        consecutive_number_generator.reset()
        
    @httpretty.activate
    def test_redirect_handler(self):
        """
        Test the redirect handler using urllib2
        """
        httpretty.register_uri(httpretty.GET, self.REDIR_SRC,
                               body='', status=FOUND,
                               adding_headers={'Location': self.REDIR_DEST})

        httpretty.register_uri(httpretty.GET, self.REDIR_DEST,
                               body=self.OK_BODY, status=FOUND)

        redirect_url = URL(self.REDIR_SRC)
        opener = urllib2.build_opener(HTTP30XHandler)
        
        request = urllib2.Request(redirect_url.url_string)

        # This is because the 30x handler doesn't implement default error handling
        # which is in another part of the w3af framework and this is just a urllib2
        # level test
        self.assertRaises(urllib2.HTTPError, opener.open, request)

    @httpretty.activate
    def test_handler_order(self):
        """
        Get an instance of the extended urllib and verify that the redirect
        handler still works, even when mixed with all the other handlers.
        """
        httpretty.register_uri(httpretty.GET, self.REDIR_SRC,
                               body='', status=FOUND,
                               adding_headers={'Location': self.REDIR_DEST})

        httpretty.register_uri(httpretty.GET, self.REDIR_DEST,
                               body=self.OK_BODY, status=FOUND)

        # Configure the handler
        redirect_url = URL(self.REDIR_SRC)
        
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(redirect_url)
        response = opener.open(request)
        
        self.assertEqual(response.code, FOUND)
        self.assertEqual(response.id, 1)


class TestRedirectHandlerExtendedUrllib(unittest.TestCase):
    """
    Test the redirect handler using ExtendedUrllib
    """
    REDIR_DEST = 'http://w3af.org/dest'
    REDIR_SRC = 'http://w3af.org/src'
    OK_BODY = 'Body!'

    def setUp(self):
        consecutive_number_generator.reset()
        self.uri_opener = ExtendedUrllib()

    def tearDown(self):
        self.uri_opener.end()

    @httpretty.activate
    def test_redirect_302_simple_no_follow(self):

        httpretty.register_uri(httpretty.GET, self.REDIR_SRC,
                               body='', status=FOUND,
                               adding_headers={'Location': self.REDIR_DEST})

        redirect_src = URL(self.REDIR_SRC)
        response = self.uri_opener.GET(redirect_src)

        location, _ = response.get_headers().iget('location')
        self.assertEqual(location, self.REDIR_DEST)
        self.assertEqual(response.get_code(), FOUND)
        self.assertEqual(response.get_id(), 1)

    @httpretty.activate
    def test_redirect_302_simple_follow(self):

        httpretty.register_uri(httpretty.GET, self.REDIR_SRC,
                               body='', status=FOUND,
                               adding_headers={'Location': self.REDIR_DEST})

        httpretty.register_uri(httpretty.GET, self.REDIR_DEST,
                               body=self.OK_BODY, status=200)

        redirect_src = URL(self.REDIR_SRC)
        response = self.uri_opener.GET(redirect_src, follow_redirects=True)

        self.assertEqual(response.get_code(), OK)
        self.assertEqual(response.get_body(), self.OK_BODY)
        self.assertEqual(response.get_redir_uri(), URL(self.REDIR_DEST))
        self.assertEqual(response.get_url(), URL(self.REDIR_SRC))
        self.assertEqual(response.get_id(), 2)

    @httpretty.activate
    def test_redirect_301_loop(self):

        httpretty.register_uri(httpretty.GET, self.REDIR_SRC,
                               body='', status=MOVED_PERMANENTLY,
                               adding_headers={'Location': self.REDIR_DEST})

        httpretty.register_uri(httpretty.GET, self.REDIR_DEST,
                               body='', status=MOVED_PERMANENTLY,
                               adding_headers={'URI': self.REDIR_SRC})

        redirect_src = URL(self.REDIR_SRC)
        response = self.uri_opener.GET(redirect_src, follow_redirects=True)

        # At some point the handler detects a loop and stops
        self.assertEqual(response.get_code(), MOVED_PERMANENTLY)
        self.assertEqual(response.get_body(), '')
        self.assertEqual(response.get_id(), 9)

    @httpretty.activate
    def test_redirect_302_without_location_returns_302_response(self):
        # Breaks the RFC
        httpretty.register_uri(httpretty.GET, self.REDIR_SRC,
                               body='', status=FOUND)

        redirect_src = URL(self.REDIR_SRC)
        response = self.uri_opener.GET(redirect_src, follow_redirects=True)

        # Doesn't follow the redirects
        self.assertEqual(response.get_code(), FOUND)
        self.assertEqual(response.get_body(), '')
        self.assertEqual(response.get_id(), 1)

    @httpretty.activate
    def test_redirect_no_follow_file_proto(self):
        httpretty.register_uri(httpretty.GET, self.REDIR_SRC,
                               body='', status=FOUND,
                               adding_headers={'Location':
                                               'file:///etc/passwd'})

        redirect_src = URL(self.REDIR_SRC)
        response = self.uri_opener.GET(redirect_src, follow_redirects=True)

        self.assertEqual(response.get_code(), FOUND)
        self.assertEqual(response.get_body(), '')
        self.assertEqual(response.get_url(), URL(self.REDIR_SRC))
        self.assertEqual(response.get_id(), 1)
