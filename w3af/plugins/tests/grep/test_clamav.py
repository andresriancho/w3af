"""
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

"""
import time
import unittest
from itertools import repeat

import pyclamd
from mock import patch, Mock

import w3af.core.data.kb.knowledge_base as kb
from w3af.plugins.grep.clamav import clamav
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.ci.moth import get_moth_http


class TestClamAV(unittest.TestCase):

    def setUp(self):
        pool = Pool(3)
        
        self.plugin = clamav()
        self.plugin.set_worker_pool(pool)
        
        kb.kb.clear('clamav', 'malware')

    def tearDown(self):
        self.plugin.end()

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_clamav_eicar(self, *args):
        body = pyclamd.ClamdAgnostic().EICAR()
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        
        self.plugin.grep(request, response)
        
        # Let the worker pool wait for the clamd response, this is done by
        # the core when run in a real scan
        self.plugin.worker_pool.close()
        self.plugin.worker_pool.join()
        
        findings = kb.kb.get('clamav', 'malware')
        
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        
        self.assertEqual(finding.get_name(), 'Malware identified')
        self.assertIn('ClamAV identified malware', finding.get_desc())
        self.assertEqual(finding.get_url().url_string, url.url_string)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_clamav_empty(self, *args):
        body = ''
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        
        self.plugin.grep(request, response)

        # Let the worker pool wait for the clamd response, this is done by
        # the core when run in a real scan
        self.plugin.worker_pool.close()
        self.plugin.worker_pool.join()

        findings = kb.kb.get('clamav', 'malware')
        
        self.assertEqual(len(findings), 0, findings)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_clamav_workers(self, *args):
        
        WAIT_TIME = 3
        DELTA = WAIT_TIME * 0.1
        
        # Prepare the mocked plugin
        def wait(x, y):
            time.sleep(WAIT_TIME)
        
        self.plugin._is_properly_configured = Mock(return_value=True)
        self.plugin._scan_http_response = wait
        self.plugin._report_result = lambda x: 42
        start_time = time.time()
        
        for i in xrange(3):
            body = ''
            url = URL('http://www.w3af.com/%s' % i)
            headers = Headers([('content-type', 'text/html')])
            response = HTTPResponse(200, body, headers, url, url, _id=1)
            request = FuzzableRequest(url, method='GET')
            
            self.plugin.grep(request, response)

        # Let the worker pool wait for the clamd response, this is done by
        # the core when run in a real scan
        self.plugin.worker_pool.close()
        self.plugin.worker_pool.join()

        end_time = time.time()
        time_spent = end_time - start_time

        findings = kb.kb.get('clamav', 'malware')
        
        self.assertEqual(len(findings), 0, findings)
        self.assertLessEqual(time_spent, WAIT_TIME + DELTA)

    @patch('w3af.plugins.grep.code_disclosure.is_404', side_effect=repeat(False))
    def test_no_clamav_eicar(self, *args):
        body = pyclamd.ClamdAgnostic().EICAR()
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

 
class TestClamAVScan(PluginTest):
 
    target_url = get_moth_http('/grep/clamav/')

    _run_configs = {          
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('clamav'),),
                'crawl': (
                    PluginConfig('web_spider',
                    ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        },        
    }

    def setUp(self):
        self.plugin = clamav()
        super(TestClamAVScan, self).setUp()
        
    def tearDown(self):
        super(TestClamAVScan, self).tearDown()
        self.plugin.end()
        
    def test_found_vuln(self):
        """
        Test to validate case in which malware is identified while crawling.
        """
        #Configure and run test case
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        findings = kb.kb.get('clamav', 'malware')
        
        self.assertEqual(len(findings), 4)
        
        EXPECTED_FILES = ('eicar.com.txt',
                          'eicar.com',
                          'eicarcom2.zip',
                          'eicar_com.zip')
        
        for finding in findings:
            self.assertIn(finding.get_url().get_file_name(), EXPECTED_FILES)
            self.assertEqual(finding.get_name(), 'Malware identified')
            self.assertIn('ClamAV identified malware', finding.get_desc())