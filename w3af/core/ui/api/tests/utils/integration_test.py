"""
integration_unittest.py

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
import time
import signal
import fnmatch
import logging
import tempfile
import unittest
import requests

from w3af.core.ui.api.tests.utils.api_process import start_api


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        # Disable requests logging
        logging.getLogger('requests').setLevel(logging.WARNING)

        self.process, self.port, self.api_url, self.api_auth = start_api()
        self.headers = {'Content-type': 'application/json',
                        'Accept': 'application/json'}

        # Clear the crashes before we start
        tempdir = tempfile.gettempdir()

        for _file in os.listdir(tempdir):
            if fnmatch.fnmatch(_file, 'w3af-crash*.txt'):
                os.unlink(os.path.join(tempdir, _file))

    def tearDown(self):
        os.killpg(self.process.pid, signal.SIGTERM)

        tempdir = tempfile.gettempdir()

        for _file in os.listdir(tempdir):
            if fnmatch.fnmatch(_file, 'w3af-crash*.txt'):
                crash = file(os.path.join(tempdir, _file)).read()

                # https://circleci.com/gh/andresriancho/w3af/2041
                if 'failing_spider' in crash:
                    continue

                msg = 'Found w3af crash file from REST API!\n\n'
                msg += crash
                self.assertTrue(False, msg)

    def wait_until_running(self):
        """
        Wait until the scan is in Running state
        :return: The HTTP response
        """
        for _ in xrange(10):
            time.sleep(0.5)

            response = requests.get('%s/scans/' % self.api_url, 
                                    auth=self.api_auth,
                                    verify=False)
                                    
            self.assertEqual(response.status_code, 200, response.text)
            if response.json()['items'][0]['status'] != 'Stopped':
                return response

        raise RuntimeError('Timeout waiting for scan to run')

    def wait_until_finish(self, wait_loops=100):
        """
        Wait until the scan is in Stopped state
        :return: The HTTP response
        """
        for _ in xrange(wait_loops):
            time.sleep(0.5)

            response = requests.get('%s/scans/' % self.api_url, 
                                    auth=self.api_auth,
                                    verify=False)
            self.assertEqual(response.status_code, 200, response.text)
            if response.json()['items'][0]['status'] != 'Running':
                return response

        raise RuntimeError('Timeout waiting for scan to run')

    def create_assert_message(self):
        """
        :return: A string with a message I can use to debug issues, contains
                 the scan log information available in the REST API (if any)
        """
        response = requests.get('%s/scans/' % self.api_url, 
                                auth=self.api_auth,
                                verify=False)
        scan_id = response.json()['items'][0]['id']

        response = requests.get('%s/scans/%s/log' % (self.api_url, scan_id),
                                auth=self.api_auth,
                                verify=False)
        scan_log = '\n'.join([m['message'] for m in response.json()['entries']])

        self.maxDiff = None
        return 'Assertion failed! The scan log contains:\n\n%s' % scan_log
