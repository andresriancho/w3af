"""
api_unittest.py

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
import time
import base64
import hashlib
import unittest

from w3af.core.ui.api import app
from w3af.core.ui.api.db.master import SCANS


class APIUnitTest(unittest.TestCase):
    PASSWORD = 'password'
    AUTHORIZATION = base64.b64encode('%s:%s' % ('admin', PASSWORD))
    HEADERS = {'Content-type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'Basic %s' % AUTHORIZATION}

    def setUp(self):
        # Raise exceptions
        app.config['TESTING'] = True
        app.testing = True

        # Configure authentication
        app.config['PASSWORD'] = hashlib.sha512(self.PASSWORD).hexdigest()
        app.config['USERNAME'] = 'admin'

        self.app = app.test_client()

    def tearDown(self):
        """
        Since the API does not support concurrent scans we need to cleanup
        everything before starting a new scan/test.
        """
        for scan_id, scan_info in SCANS.iteritems():
            if scan_info is not None:
                scan_info.w3af_core.stop()
                scan_info.w3af_core.cleanup()
                SCANS[scan_id] = None

    def wait_until_running(self):
        """
        Wait until the scan is in Running state
        :return: The HTTP response
        """
        for _ in xrange(10):
            time.sleep(0.5)

            response = self.app.get('/scans/', headers=self.HEADERS)

            self.assertEqual(response.status_code, 200, response.data)
            if json.loads(response.data)['items'][0]['status'] != 'Stopped':
                return response

        raise RuntimeError('Timeout waiting for scan to run')

    def wait_until_finish(self, wait_loops=150):
        """
        Wait until the scan is in Stopped state
        :return: The HTTP response
        """
        status = None

        for _ in xrange(wait_loops):
            time.sleep(0.5)

            response = self.app.get('/scans/', headers=self.HEADERS)
            self.assertEqual(response.status_code, 200, response.data)

            status = json.loads(response.data)['items'][0]['status']
            if status != 'Running':
                return response

        msg = 'Timeout waiting for scan to finish, latest status is: "%s"'
        raise RuntimeError(msg % status)