# -*- coding: utf-8 -*-
'''
test_xurllib_integration.py

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
import unittest

from nose.plugins.attrib import attr

from core.data.url.opener_settings import OpenerSettings
from core.data.url.extended_urllib import ExtendedUrllib
from core.data.parsers.url import URL


@attr('moth')
class TestXUrllibIntegration(unittest.TestCase):

    MOTH_MESSAGE = 'Welcome to the moth homepage!'

    def setUp(self):
        self.uri_opener = ExtendedUrllib()
        
    def test_ntlm_auth_not_configured(self):
        self.uri_opener = ExtendedUrllib()
        url = URL("http://moth/w3af/core/ntlm_auth/ntlm_v1/")
        http_response = self.uri_opener.GET(url, cache=False)
        self.assertIn('Must authenticate.', http_response.body)

    def test_ntlm_auth_valid_creds(self):
        
        self.uri_opener = ExtendedUrllib()
        
        settings = OpenerSettings()
        options = settings.get_options()
        ntlm_domain = options['ntlm_auth_domain'] 
        ntlm_user = options['ntlm_auth_user']
        ntlm_pass = options['ntlm_auth_passwd']
        ntlm_url = options['ntlm_auth_url']
        
        ntlm_domain.set_value('moth') 
        ntlm_user.set_value('admin')
        ntlm_pass.set_value('admin')
        ntlm_url.set_value('http://moth/w3af/core/ntlm_auth/ntlm_v1/')
        
        settings.set_options(options)
        self.uri_opener.settings = settings
        
        url = URL("http://moth/w3af/core/ntlm_auth/ntlm_v1/")
        http_response = self.uri_opener.GET(url, cache=False)
        self.assertIn('You are admin from MOTH/', http_response.body)

    def test_gzip(self):
        url = URL('http://www.google.com.ar/')
        res = self.uri_opener.GET(url, cache=False)
        headers = res.get_headers()
        content_encoding, _ = headers.iget('content-encoding', '')
        test_res = 'gzip' in content_encoding or \
                   'compress' in content_encoding
        self.assertTrue(test_res, content_encoding)

    def test_get_cookies(self):
        self.assertEqual(len([c for c in self.uri_opener.get_cookies()]), 0)

        url_sends_cookie = URL(
            'http://moth/w3af/core/cookie_handler/set-cookie.php')
        self.uri_opener.GET(url_sends_cookie, cache=False)

        self.assertEqual(len([c for c in self.uri_opener.get_cookies()]), 1)
        cookie = [c for c in self.uri_opener.get_cookies()][0]
        self.assertEqual('moth.local', cookie.domain)
