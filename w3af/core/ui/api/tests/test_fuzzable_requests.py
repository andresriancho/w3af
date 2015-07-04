"""
test_fuzzable_requests.py

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
import base64
import requests

from w3af.core.ui.api.tests.utils.api_unittest import APIUnitTest
from w3af.core.ui.api.tests.utils.test_profile import get_test_profile

EXPECTED_FUZZABLE_REQUESTS = [
    'GET http://127.0.0.1:8000/audit/sql_injection/ HTTP/1.1\r\nReferer: http://127.0.0.1:8000/\r\n\r\n',
    'GET http://127.0.0.1:8000/audit/sql_injection/where_integer_form.py HTTP/1.1\r\nReferer: http://127.0.0.1:8000/\r\n\r\n',
    'POST http://127.0.0.1:8000/audit/sql_injection/where_integer_form.py HTTP/1.1\r\nReferer: http://127.0.0.1:8000/\r\n\r\ntext=&Submit=Submit',
    'GET http://127.0.0.1:8000/audit/sql_injection/where_string_single_qs.py?uname=pablo HTTP/1.1\r\nReferer: http://127.0.0.1:8000/\r\n\r\n',
    'GET http://127.0.0.1:8000/audit/sql_injection/ HTTP/1.1\r\n\r\n',
    'GET http://127.0.0.1:8000/audit/sql_injection/where_integer_qs.py?id=1 HTTP/1.1\r\nReferer: http://127.0.0.1:8000/\r\n\r\n',
]


class FuzzableRequestsTest(APIUnitTest):

    def test_fuzzable_request_list(self):
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
        response = requests.get('%s/scans/%s/fuzzable-requests/' % args,
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        encoded_fuzzable_requests_items = response.json()['items']
        decoded_fuzzable_requests = []

        for encoded_fr in encoded_fuzzable_requests_items:
            decoded_fr = base64.b64decode(encoded_fr)
            decoded_fuzzable_requests.append(decoded_fr)

        self.assertEqual(set(decoded_fuzzable_requests),
                         set(EXPECTED_FUZZABLE_REQUESTS))


