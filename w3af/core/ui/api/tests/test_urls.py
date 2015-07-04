"""
test_urls.py

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


class URLTest(APIUnitTest):

    def test_url_list(self):
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
        # Get all the URLs that the scanner found
        #
        args = (self.api_url, scan_id)
        response = requests.get('%s/scans/%s/urls/' % args, auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        url_items = response.json()['items']

        expected_urls = [target_url,
                         u'%s/where_integer_qs.py' % target_url[:-1],
                         u'%s/where_string_single_qs.py' % target_url[:-1],
                         u'%s/where_integer_form.py' % target_url[:-1]]
        self.assertEqual(set(url_items), set(expected_urls))

