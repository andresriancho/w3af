"""
test_scan.py

Copyright 2015 Andres Riancho

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
import json
import time
import signal
import fnmatch
import logging
import tempfile
import unittest
import requests

from w3af.core.ui.api.tests.utils.api_process import start_api
from w3af.core.ui.api.tests.utils.test_profile import (get_test_profile,
                                                       get_expected_vuln_names,
                                                       get_expected_vuln_urls)


class APIScanTest(unittest.TestCase):
    def setUp(self):
        # Disable requests logging
        logging.getLogger('requests').setLevel(logging.WARNING)

        self.process, self.port, self.api_url = start_api()
        self.headers = {'Content-type': 'application/json',
                        'Accept': 'application/json'}

    def tearDown(self):
        os.killpg(self.process.pid, signal.SIGTERM)

        for _file in os.listdir(tempfile.gettempdir()):
            if fnmatch.fnmatch(_file, 'w3af-crash*.txt'):
                self.assertTrue(False, 'Found w3af crash file from REST API!')

    def wait_until_running(self):
        """
        Wait until the scan is in Running state
        :return: The HTTP response
        """
        for _ in xrange(10):
            time.sleep(0.5)

            result = requests.get('%s/scans/' % self.api_url)
            self.assertEqual(result.status_code, 200, result.text)
            if result.json()['items'][0]['status'] != 'Stopped':
                return result

        raise RuntimeError('Timeout waiting for scan to run')

    def wait_until_finish(self):
        """
        Wait until the scan is in Stopped state
        :return: The HTTP response
        """
        for _ in xrange(100):
            time.sleep(0.5)

            result = requests.get('%s/scans/' % self.api_url)
            self.assertEqual(result.status_code, 200, result.text)
            if result.json()['items'][0]['status'] != 'Running':
                return result

        raise RuntimeError('Timeout waiting for scan to run')

    def test_start_simple_scan(self):
        profile, target_url = get_test_profile()
        data = {'scan_profile': profile,
                'target_urls': [target_url]}
        response = requests.post('%s/scans/' % self.api_url,
                                 data=json.dumps(data),
                                 headers=self.headers)

        self.assertEqual(response.json(), {u'message': u'Success',
                                           u'href': u'/scans/0',
                                           u'id': 0})
        self.assertEqual(response.status_code, 201)

        # Iterate until the scan is in Running state
        response = self.wait_until_running()

        self.assertEqual(response.status_code, 200, response.text)
        list_response = {u'items': [{u'href': u'/scans/0',
                                     u'id': 0,
                                     u'status': u'Running',
                                     u'errors': False,
                                     u'target_urls': [target_url]}]}
        self.assertEqual(response.json(), list_response)

        # Wait until the scanner finds the vulnerabilities
        self.wait_until_finish()

        result = requests.get('%s/kb/' % self.api_url)
        self.assertEqual(result.status_code, 200, result.text)

        vuln_summaries = result.json()['items']
        names = set([v['name'] for v in vuln_summaries])
        urls = set([v['url'] for v in vuln_summaries])

        self.assertEqual(4, len(vuln_summaries))
        self.assertEqual(names, set(get_expected_vuln_names()))
        self.assertEqual(urls, set(get_expected_vuln_urls(target_url)))
