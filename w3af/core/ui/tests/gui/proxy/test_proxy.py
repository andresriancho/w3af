"""
test_proxy.py

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
import os
import urllib2
import threading

from w3af.core.ui.tests.gui import GUI_TEST_ROOT_PATH
from w3af.core.ui.tests.wrappers.xpresser_unittest import XpresserUnittest

from w3af.core.data.url.tests.helpers.http_daemon import HTTPDaemon


class TestProxy(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'proxy', 'images')
    EXTRA_IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'tools_menu', 'images')
    
    def setUp(self):
        XpresserUnittest.setUp(self)
        self.click('proxy-menu-icon')
        self.find('proxy-tabs')

        self.http_daemon = HTTPDaemon()
        self.http_daemon.start()
        self.http_daemon.wait_for_start()

        proxy_url = '127.0.0.1:8080'
        proxy_support = urllib2.ProxyHandler({'http': proxy_url,
                                              'https': proxy_url})
        self.opener = urllib2.build_opener(proxy_support)
        
    def tearDown(self):
        self.click('close-with-cross')
        self.click('yes')
        
        self.http_daemon.shutdown()
        
        XpresserUnittest.tearDown(self)
    
    def test_basic_forwarding(self):
        port = self.http_daemon.get_port()
        http_response = self.opener.open('http://127.0.0.1:%s/foo' % port).read()
        self.assertEqual('ABCDEF\n', http_response)

    def test_intercept(self):
        
        self.click('intercept')

        def ui_clicker():
            # Click on the proxy button that will forward the request
            try:
                self.find('GET_http')
                self.click('send-request')
                self.find('200_OK')
                self.click('next_request')
                self.find('empty_intercept')
            except:
                pass

        t = threading.Thread(target=ui_clicker)
        t.start()

        port = self.http_daemon.get_port()
        http_response = self.opener.open('http://127.0.0.1:%s/foo' % port).read()
        self.assertEqual('ABCDEF\n', http_response)

        t.join()