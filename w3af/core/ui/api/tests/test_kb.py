"""
test_kb.py

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
from w3af.core.ui.api.tests.utils.test_profile import get_test_profile


class KBApiTest(APIUnitTest):

    def test_kb_filters(self):
        profile, target_url = get_test_profile()
        data = {'scan_profile': profile,
                'target_urls': [target_url]}
        response = requests.post('%s/scans/' % self.api_url,
                                 auth=self.api_auth,
                                 data=json.dumps(data),
                                 headers=self.headers)

        scan_id = response.json()['id']

        #
        # Wait until the scanner finishes and assert the vulnerabilities
        #
        self.wait_until_running()
        self.wait_until_finish()

        #
        # Name filter
        #
        args = (self.api_url, scan_id)
        response = requests.get('%s/scans/%s/kb/?name=SQL%%20Injection' % args,
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        vuln_items = response.json()['items']
        self.assertEqual(4, len(vuln_items), self.create_assert_message())

        response = requests.get('%s/scans/%s/kb/?name=Foo' % args,
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        vuln_items = response.json()['items']
        self.assertEqual(0, len(vuln_items))

        #
        # URL filter
        #
        extra_args = (self.api_url, scan_id, target_url)
        response = requests.get('%s/scans/%s/kb/?url=%s' % extra_args,
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        vuln_items = response.json()['items']
        self.assertEqual(4, len(vuln_items))

        response = requests.get('%s/scans/%s/kb/?url=http://google.com/' % args,
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        vuln_items = response.json()['items']
        self.assertEqual(0, len(vuln_items))

        #
        # Combined filter
        #
        qs = '%s/scans/%s/kb/?url=%s&name=SQL%%20injection'
        response = requests.get(qs % extra_args,
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        vuln_items = response.json()['items']
        self.assertEqual(4, len(vuln_items))
