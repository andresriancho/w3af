# -*- coding: utf-8 -*-
"""
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
"""
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.url.opener_settings import OpenerSettings
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.ci.moth import get_moth_http, get_moth_https
from w3af.core.controllers.daemons.proxy import Proxy, ProxyHandler


@attr('moth')
@attr('smoke')
class TestExtendedUrllibProxy(unittest.TestCase):

    MOTH_MESSAGE = '<title>moth: vulnerable web application</title>'

    def setUp(self):
        self.uri_opener = ExtendedUrllib()
        
        # Start the proxy daemon
        self._proxy = Proxy('127.0.0.2', 0, ExtendedUrllib(), ProxyHandler)
        self._proxy.start()
        self._proxy.wait_for_start()
        
        port = self._proxy.get_port()
        
        # Configure the proxy
        settings = OpenerSettings()
        options = settings.get_options()
        proxy_address_opt = options['proxy_address']
        proxy_port_opt = options['proxy_port']
        
        proxy_address_opt.set_value('127.0.0.2')
        proxy_port_opt.set_value(port)
        
        settings.set_options(options)
        self.uri_opener.settings = settings
    
    def tearDown(self):
        self.uri_opener.end()
        
    def test_http_default_port_via_proxy(self):
        # TODO: Write this test
        pass

    def test_http_port_specification_via_proxy(self):
        self.assertEqual(self._proxy.total_handled_requests, 0)

        url = URL(get_moth_http())
        http_response = self.uri_opener.GET(url, cache=False)

        self.assertIn(self.MOTH_MESSAGE, http_response.body)
        self.assertEqual(self._proxy.total_handled_requests, 1)

    def test_https_via_proxy(self):
        self.assertEqual(self._proxy.total_handled_requests, 0)

        url = URL(get_moth_https())
        http_response = self.uri_opener.GET(url, cache=False)

        self.assertIn(self.MOTH_MESSAGE, http_response.body)
        self.assertEqual(self._proxy.total_handled_requests, 1)

    def test_offline_port_via_proxy(self):
        url = URL('http://127.0.0.1:8181/')
        http_response = self.uri_opener.GET(url, cache=False)
        self.assertEqual(http_response.get_code(), 500)
        self.assertIn('Connection refused', http_response.body)
    
    def test_POST_via_proxy(self):
        url = URL(get_moth_http('/audit/xss/simple_xss_form.py'))
        http_response = self.uri_opener.POST(url, data='text=123456abc', cache=False)
        self.assertIn('123456abc', http_response.body)