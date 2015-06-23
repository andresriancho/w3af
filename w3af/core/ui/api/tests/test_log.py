"""
test_log.py

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
import json
import requests

from w3af.core.ui.api.tests.utils.api_unittest import APIUnitTest
from w3af.core.ui.api.tests.utils.test_profile import (get_test_profile,
                                                       SLOW_TEST_PROFILE)


class ApiScanLogTest(APIUnitTest):

    def test_scan_log(self):
        profile, target_url = get_test_profile(SLOW_TEST_PROFILE)
        data = {'scan_profile': profile,
                'target_urls': [target_url]}
        requests.post('%s/scans/' % self.api_url,
                      data=json.dumps(data),
                      headers=self.headers)

        #
        # Wait until the scanner finishes and assert the vulnerabilities
        #
        self.wait_until_running()
        self.wait_until_finish(500)

        #
        # Get the scan log
        #
        response = requests.get('%s/scans/0/log' % self.api_url)
        self.assertEqual(response.status_code, 200, response.text)

        log_data_page_0 = response.json()
        self.assertEqual(len(log_data_page_0['entries']), 200)
        self.assertEqual(log_data_page_0['more'], True)
        self.assertEqual(log_data_page_0['next'], 1)

        zero_entry = log_data_page_0['entries'][0]
        self.assertEqual(zero_entry['message'], u'Called w3afCore.start()')
        self.assertEqual(zero_entry['severity'], None)
        self.assertEqual(zero_entry['type'], 'debug')
        self.assertIsNotNone(zero_entry['time'])

        response = requests.get('%s/scans/0/log?page=1' % self.api_url)
        self.assertEqual(response.status_code, 200, response.text)

        self.assertNotEqual(log_data_page_0['entries'],
                            response.json()['entries'])
