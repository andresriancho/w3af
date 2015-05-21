"""
test_fuzzy_request_editor.py

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

from w3af.core.data.parsers.doc.http_request_parser import http_request_parser
from w3af.core.ui.tests.gui import GUI_TEST_ROOT_PATH
from w3af.core.ui.tests.wrappers.xpresser_unittest import XpresserUnittest
from w3af.core.data.url.tests.helpers.http_daemon import HTTPDaemon


# TODO: Code duplication
#
# Tried to do this the right way, by adding the import at the beginning
# of the file:
#
#from w3af.core.ui.gui.tools.manual_requests import MANUAL_REQUEST_EXAMPLE
#
# But it fails because of the pygtk vs. gi stuff... 
FUZZY_REQUEST_EXAMPLE = """\
GET http://localhost/$xrange(10)$ HTTP/1.0
Host: www.some_host.com
User-Agent: w3af.org
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
"""


class TestFuzzyRequestEditor(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'fuzzy_request_editor', 'images')
    EXTRA_IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'tools_menu', 'images')
    
    def setUp(self):
        XpresserUnittest.setUp(self)
        self.click('fuzzy-requests-icon')
        self.find('fuzzy-requests-tabs')

    def tearDown(self):
        self.click('close-with-cross')
        XpresserUnittest.tearDown(self)
    
    def test_offline_url(self):
        self.double_click('localhost')
        self.type('moth:8081', False)
        
        self.click('play')
        self.find('error')
        
        # Close the error dialog
        self.type(['<Enter>',], False)

    
    def test_invalid_request(self):
        self.double_click('localhost')
        self.type('moth:8081', False)
        
        # Move to the beginning and break the syntax
        self.type(['<PgUp>',], False)
        self.type('x', False)
        self.type(['<Enter>',], False)
        
        self.find('send-disabled')
        
        # Remove the ugly stuff
        self.type(['<PgUp>',], False)
        self.type(['<Delete>',], False)
        self.type(['<Delete>',], False)
        self.sleep(1)
        
        self.not_find('send_disabled')
        
        self.click('play')
        self.find('error')
        
        # Close the error dialog
        self.type(['<Enter>',], False)

    
    def test_GET_request(self):
        self.http_daemon = HTTPDaemon()
        self.http_daemon.start()
        self.http_daemon.wait_for_start()
        
        #
        #    Send the request to our server using the GUI
        #
        self.double_click('localhost')
        self.type('127.0.0.1:%s' % self.http_daemon.get_port(), False)
        
        self.click('play')
               
        # Wait until we actually get the response, and verify we got the
        # response body we expected:
        self.click('response_tab')
        self.find('abcdef')
        self.find('200_OK')
        
        #
        #    Assert that it's what we really expected
        #
        requests = self.http_daemon.requests
        self.assertEqual(len(requests), 10)
        
        head, postdata = FUZZY_REQUEST_EXAMPLE, ''
        parsed_request = http_request_parser(head, postdata)
        
        for i, daemon_request in enumerate(self.http_daemon.requests):

            self.assertEqual('/%s' % i, daemon_request.path)
            self.assertEqual(parsed_request.get_method(), daemon_request.command)
        
            for header_name, header_value in parsed_request.get_headers().iteritems():
                self.assertIn(header_name.lower(), daemon_request.headers)
                self.assertEqual(header_value, daemon_request.headers[header_name.lower()])
            
        self.http_daemon.shutdown()
    
    def test_POST_request(self):
        self.http_daemon = HTTPDaemon()
        self.http_daemon.start()
        self.http_daemon.wait_for_start()
        
        #
        #    Send the request to our server using the GUI
        #
        self.double_click('localhost')
        self.type('127.0.0.1:%s' % self.http_daemon.get_port(), False)
        
        # Move to the beginning
        self.type(['<PgUp>',], False)
        
        # Replace GET with POST
        self.type(['<Delete>',], False)
        self.type(['<Delete>',], False)
        self.type(['<Delete>',], False)
        self.type('POST', False)
        
        # Move to the end (postdata)
        self.type(['<PgDn>',], False)
        post_data = 'foo=bar&spam=eggs'
        self.type(post_data, False)
        
        self.click('play')
        
        # Wait until we actually get the response, and verify we got the
        # response body we expected:
        self.click('response_tab')
        self.find('abcdef')
        self.find('200_OK')
        
        #
        #    Assert that it's what we really expected
        #
        requests = self.http_daemon.requests
        self.assertEqual(len(requests), 10)
        
        head, postdata = FUZZY_REQUEST_EXAMPLE, ''
        parsed_request = http_request_parser(head, postdata)
        
        for i, daemon_request in enumerate(self.http_daemon.requests):

            self.assertEqual('/%s' % i, daemon_request.path)
            self.assertEqual('POST', daemon_request.command)
        
            for header_name, header_value in parsed_request.get_headers().iteritems():
                self.assertIn(header_name.lower(), daemon_request.headers)
                self.assertEqual(header_value, daemon_request.headers[header_name.lower()])
        
        self.http_daemon.shutdown()
