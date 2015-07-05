"""
test_version.py

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

from w3af.core.ui.api.tests.utils.api_unittest import APIUnitTest


class VersionTest(APIUnitTest):

    def test_get_version(self):
        #
        # Name filter
        #
        response = self.app.get('/version', headers=self.HEADERS)
        self.assertEqual(response.status_code, 200, response.data)

        version_dict = json.loads(response.data)
        self.assertIn('version', version_dict)
        self.assertIn('revision', version_dict)
        self.assertIn('branch', version_dict)
        self.assertIn('dirty', version_dict)
