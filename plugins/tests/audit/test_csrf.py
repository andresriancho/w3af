'''
test_csrf.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
from ..helper import PluginTest, PluginConfig
from nose.plugins.skip import SkipTest

from plugins.audit.csrf import csrf

from core.data.url.HTTPResponse import HTTPResponse
from core.data.parsers.urlParser import url_object
from core.data.request.fuzzable_request import FuzzableRequest
from core.data.url.xUrllib import xUrllib


class TestCSRF(PluginTest):
    
    target_url = 'http://moth/w3af/audit/csrf/'
    
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                 'audit': (PluginConfig('csrf'),),
                 'crawl': (
                      PluginConfig(
                          'web_spider',
                          ('onlyForward', True, PluginConfig.BOOL)),
                  )
                 }
            }
        }
    
    def test_resp_is_equal(self):
        x = csrf()
        url = url_object('http://www.w3af.com/')
        headers = {'content-type': 'text/html'}
        
        r1 = HTTPResponse(200, 'body' , headers, url, url)
        r2 = HTTPResponse(404, 'body' , headers, url, url)
        self.assertFalse( x._is_resp_equal(r1, r2) )
        
        r1 = HTTPResponse(200, 'a' , headers, url, url)
        r2 = HTTPResponse(200, 'b' , headers, url, url)
        self.assertFalse( x._is_resp_equal(r1,r2) )
        
        r1 = HTTPResponse(200, 'a' , headers, url, url)
        r2 = HTTPResponse(200, 'a' , headers, url, url)
        self.assertTrue( x._is_resp_equal(r1,r2) )
        
    def test_is_suitable(self):
        x = csrf()
        uri_opener = xUrllib()
        x.set_url_opener( uri_opener )
        
        url = url_object('http://www.w3af.com/')
        req = FuzzableRequest(url, method='GET')
        self.assertFalse( x._is_suitable( req )[0] )

        url = url_object('http://www.w3af.com/?id=3')
        req = FuzzableRequest(url, method='GET')
        self.assertFalse( x._is_suitable( req )[0] )

        url_sends_cookie = url_object('http://moth/w3af/core/cookie_handler/set-cookie.php')
        uri_opener.GET( url_sends_cookie )

        url = url_object('http://www.w3af.com/?id=3')
        req = FuzzableRequest(url, method='GET')
        self.assertTrue( x._is_suitable( req )[0] )


    def test_found_csrf(self):
        raise SkipTest('Still need to work on this in order to make it work')

        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('csrf', 'csrf')
        self.assertEquals(2, len(vulns))

        EXPECTED = [
            ('vulnerable/buy.php'),
            ('vulnerable-rnd/buy.php'),
        ]

        self.assertEquals( set(EXPECTED),
                           set([ v.getURL().getFileName() for v in vulns]) )
        self.assertTrue(all(['CSRF vulnerability' == v.getName() for v in vulns ]) )


