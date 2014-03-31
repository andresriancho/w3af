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
import unittest
import urllib2

from nose.plugins.attrib import attr

from w3af.core.controllers.misc.number_generator import consecutive_number_generator
from w3af.core.controllers.ci.moth import get_moth_http

from w3af.core.data.parsers.url import URL
from w3af.core.data.constants.response_codes import FOUND
from w3af.core.data.url.handlers.redirect import HTTP30XHandler
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url import opener_settings


class TestRedirectHandler(unittest.TestCase):

    def setUp(self):
        consecutive_number_generator.reset()
        
    @attr('moth')
    def test_redirect_handler(self):
        """Test the redirect handler using urllib2"""
        redirect_url = URL(get_moth_http('/audit/global_redirect/redirect-header-302.py?url=/'))
        opener = urllib2.build_opener(HTTP30XHandler)
        
        request = urllib2.Request(redirect_url.url_string)
        response = opener.open(request)
        
        self.assertEqual(response.code, FOUND)

    @attr('moth')
    def test_handler_order(self):
        """Get an instance of the extended urllib and verify that the redirect
        handler still works, even when mixed with all the other handlers."""
        # Configure the handler
        redirect_url = URL(get_moth_http('/audit/global_redirect/redirect-header-302.py?url=/'))
        
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(redirect_url)
        response = opener.open(request)
        
        self.assertEqual(response.code, FOUND)
        self.assertEqual(response.id, 1)