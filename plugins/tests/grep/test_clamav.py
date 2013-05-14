'''
test_clamav.py

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
import clamd

from itertools import repeat
from functools import wraps
from mock import patch, Mock
from nose.plugins.skip import SkipTest

import core.data.kb.knowledge_base as kb

from plugins.grep.clamav import clamav
from core.data.url.HTTPResponse import HTTPResponse
from core.data.dc.headers import Headers
from core.data.request.fuzzable_request import FuzzableRequest
from core.data.parsers.url import URL


def need_clamav(meth):
    
    @wraps(meth)
    def debug(self, *args, **kwds):
        if not self.plugin._connection_test():
            raise SkipTest('No connection to clamav found.')
        
        return meth(self, *args, **kwds)
    
    return debug

    
class TestClamAV(unittest.TestCase):

    def setUp(self):
        self.plugin = clamav()
        kb.kb.clear('clamav', 'malware')

    def tearDown(self):
        self.plugin.end()

    @patch('plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    @need_clamav
    def test_clamav_eicar(self, *args):
        body = clamd.EICAR
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        
        self.plugin.grep(request, response)
        findings = kb.kb.get('clamav', 'malware')
        
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        
        self.assertEqual(finding.get_name(), 'Malware identified')
        self.assertIn('ClamAV identified malware', finding.get_desc())
        self.assertEqual(finding.get_url().url_string, url.url_string)
        

    @patch('plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    @need_clamav
    def test_clamav_empty(self, *args):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        
        self.plugin.grep(request, response)
        findings = kb.kb.get('clamav', 'malware')
        
        self.assertEqual(len(findings), 0, findings)

    @patch('plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_no_clamav_eicar(self, *args):
        body = clamd.EICAR
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        
        # Simulate that we don't have clamd running
        self.plugin._connection_test = Mock(return_value=False)
        self.plugin._scan_http_response = Mock()
        self.plugin.grep(request, response)
        findings = kb.kb.get('clamav', 'malware')
        
        self.assertEqual(len(findings), 0)
        self.assertEqual(self.plugin._scan_http_response.call_count, 0)
