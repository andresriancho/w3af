'''
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

'''
import unittest
import urllib2

from nose.plugins.attrib import attr

import core.data.kb.config as cf

from core.data.parsers.url import URL
from core.data.constants.response_codes import NO_CONTENT
from core.data.url.handlers.blacklist import BlacklistHandler
from core.data.url.HTTPRequest import HTTPRequest
from core.data.url import opener_settings


class TestBlacklistHandler(unittest.TestCase):
    
    def tearDown(self):
        cf.cf.save('non_targets', [])
    
    def test_blacklist_handler_block(self):
        '''Verify that the blacklist handler works as expected'''
        
        # Configure the handler
        blocked_url = URL('http://moth/abc/def/')
        cf.cf.save('non_targets', [blocked_url,])
        
        opener = urllib2.build_opener(BlacklistHandler)
        
        request = urllib2.Request(blocked_url.url_string)
        request.url_object = blocked_url
        response = opener.open(request)
        
        self.assertEqual(response.code, NO_CONTENT)
    
    @attr('moth')
    def test_blacklist_handler_pass(self):
        '''Verify that the blacklist handler works as expected'''
        opener = urllib2.build_opener(BlacklistHandler)
        
        request = urllib2.Request('http://moth/')
        request.url_object = URL('http://moth/')
        response = opener.open(request)
        
        self.assertEqual(response.code, 200)
    
    def test_handler_order_block(self):
        '''Get an instance of the extended urllib and verify that the blacklist
        handler still works, even when mixed with all the other handlers.'''
        # Configure the handler
        blocked_url = URL('http://moth/abc/def/')
        cf.cf.save('non_targets', [blocked_url,])
        
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(blocked_url)
        request.url_object = blocked_url
        request.cookies = True
        request.get_from_cache = False
        response = opener.open(request)
        
        self.assertEqual(response.code, NO_CONTENT)

    @attr('moth')
    def test_handler_order_pass(self):
        '''Get an instance of the extended urllib and verify that the blacklist
        handler still works, even when mixed with all the other handlers.'''
        # Configure the handler
        blocked_url = URL('http://moth/abc/def/')
        safe_url = URL('http://moth/')
        cf.cf.save('non_targets', [blocked_url,])
        
        settings = opener_settings.OpenerSettings()
        settings.build_openers()
        opener = settings.get_custom_opener()

        request = HTTPRequest(safe_url)
        request.url_object = safe_url
        request.cookies = True
        request.get_from_cache = False
        response = opener.open(request)
        
        self.assertEqual(response.code, 200)