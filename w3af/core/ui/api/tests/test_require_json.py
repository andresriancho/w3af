"""
test_require_json.py

Copyright 2016 Andres Riancho

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

from w3af.core.ui.api.middlewares.require_json import NO_HEADER, INVALID_JSON
from w3af.core.ui.api.tests.utils.api_unittest import APIUnitTest
from w3af.core.ui.api.tests.utils.test_profile import get_test_profile


class RequireJSONTest(APIUnitTest):

    def test_require_json_header(self):
        profile, target_url = get_test_profile()
        data = {'scan_profile': profile,
                'target_urls': [target_url]}

        # I'm not sending any content-type in this request
        headers = self.HEADERS.copy()
        headers.pop('Content-type')

        response = self.app.post('/scans/',
                                 data=json.dumps(data),
                                 headers=headers)

        error = json.loads(response.data)
        self.assertEqual(error['code'], 400)
        self.assertEqual(error['message'], NO_HEADER)
        self.assertEqual(response.status_code, 400)

    def test_require_json_data(self):
        response = self.app.post('/scans/',
                                 data='{3,.-1!}--',
                                 headers=self.HEADERS)

        error = json.loads(response.data)
        self.assertEqual(error['code'], 400)
        self.assertEqual(error['message'], INVALID_JSON)
        self.assertEqual(response.status_code, 400)


