"""
test_session_scan.py

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
import base64

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.ui.api.tests.utils.integration_test import IntegrationTest
from w3af.core.ui.api.tests.utils.test_profile import (get_expected_vuln_names,
                                                       get_expected_vuln_urls)


class APIScanFromSessionTest(IntegrationTest):

    def test_start_scan_from_session(self):
        plugin_settings = {
            "crawl.web_spider": {
                "only_forward": True,
                "follow_regex": ".*"},
            "audit.sqli": {}
        }
        target_url = get_moth_http('/audit/sql_injection')
        core_settings = {
            "misc": {
                "fuzz_cookies": False,
                "fuzz_form_files": True,
                "fuzz_url_filenames": False,
                "fuzz_url_parts": False,
                "fuzzed_files_extension": "gif",
                "form_fuzzing_mode": "tmb",
                "stop_on_first_exception": False,
                "max_discovery_time": 120,
                "interface": "wlan1",
                "local_ip_address": "10.1.2.24",
                "msf_location": "/opt/metasploit3/bin"},
            "http": {
                "timeout": 0,
                "ignore_session_cookies": False,
                "proxy_port": 8080,
                "user_agent": "w3af.org",
                "rand_user_agent": False,
                "max_file_size": 400000,
                "max_http_retries": 2,
                "max_requests_per_second": 0},
            "target": {
                "target": [target_url]}
            }
        response = requests.post('%s/sessions/' % self.api_url,
                                 auth = self.api_auth,
                                 headers=self.headers)

        scan_id = response.json()['id']
        self.assertEqual(response.json(), {u'message': u'Success',
                                           u'href': u'/sessions/%s' % scan_id,
                                           u'id': scan_id})
        self.assertEqual(response.status_code, 201)

        for ps in plugin_settings:
            key =  ps.split('.')
            plugin_type = key[0]
            plugin = key[1]
            plugin_settings[ps]["enabled"] = True

            r = requests.patch(
                '%s/sessions/%s/plugins/%s/%s/' % (
                    self.api_url, scan_id, plugin_type, plugin),
                auth = self.api_auth,
                data=json.dumps(plugin_settings[ps]),
                headers=self.headers)

            self.assertEqual(r.status_code, 200)

        for cs in core_settings:
            r = requests.patch(
                '%s/sessions/%s/core/%s/' % (
                    self.api_url, scan_id, cs),
                auth = self.api_auth,
                data=json.dumps(core_settings[cs]),
                headers=self.headers)

        start_scan = requests.post(
            '%s/sessions/%s/start' % (
                self.api_url, scan_id),
            auth = self.api_auth,
            headers=self.headers)

        self.assertEqual(start_scan.status_code, 200)

        #
        # Wait until the scan is in Running state
        #
        response = self.wait_until_running()

        self.assertEqual(response.status_code, 200, response.text)
        list_response = {u'items': [{u'href': u'/scans/%s' % scan_id,
                                     u'id': scan_id,
                                     u'status': u'Running',
                                     u'errors': False,
                                     u'target_urls': [target_url]}]}
        self.assertEqual(response.json(), list_response)

        #
        # Get the detailed status
        #
        response = requests.get('%s/scans/%s/status' % (self.api_url, scan_id),
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        json_data = response.json()
        self.assertEqual(json_data['is_running'], True)
        self.assertEqual(json_data['is_paused'], False)
        self.assertEqual(json_data['exception'], None)

        #
        # Wait until the scanner finishes and assert the vulnerabilities
        #
        self.wait_until_finish()

        response = requests.get('%s/scans/%s/kb/' % (self.api_url, scan_id),
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        vuln_summaries = response.json()['items']
        names = set([v['name'] for v in vuln_summaries])
        urls = set([v['url'] for v in vuln_summaries])

        self.assertEqual(4, len(vuln_summaries))
        self.assertEqual(names, set(get_expected_vuln_names()))
        self.assertEqual(urls, set(get_expected_vuln_urls(target_url)))

        #
        # Make sure I can access the vulnerability details
        #
        response = requests.get('%s/scans/%s/kb/0' % (self.api_url, scan_id),
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        vuln_info = response.json()
        self.assertEqual(vuln_info['plugin_name'], 'sqli')
        self.assertEqual(vuln_info['href'], '/scans/%s/kb/0' % scan_id)
        self.assertEqual(vuln_info['id'], 0)
        self.assertEqual(vuln_info['fix_effort'], 50)
        self.assertEqual(vuln_info['cwe_ids'], ['89'])
        self.assertEqual(vuln_info['severity'], 'High')
        self.assertEqual(vuln_info['tags'], [u'web', u'sql', u'injection',
                                             u'database', u'error'])

        #
        # Get the HTTP traffic for this vulnerability
        #
        traffic_href = vuln_info['traffic_hrefs'][0]
        response = requests.get('%s%s' % (self.api_url, traffic_href),
                                auth=self.api_auth)

        traffic_data = response.json()
        self.assertIn('request', traffic_data)
        self.assertIn('response', traffic_data)

        self.assertIn('GET ', base64.b64decode(traffic_data['request']))

        #
        # Get the scan log
        #
        response = requests.get('%s/scans/%s/log' % (self.api_url, scan_id),
                                auth=self.api_auth)
        self.assertEqual(response.status_code, 200, response.text)

        log_data = response.json()
        self.assertGreater(len(log_data['entries']), 100)
        self.assertEqual(log_data['next'], None)
        self.assertEqual(log_data['next_url'], None)

        zero_entry = log_data['entries'][0]
        self.assertEqual(zero_entry['message'], u'Called w3afCore.start()')
        self.assertEqual(zero_entry['severity'], None)
        self.assertEqual(zero_entry['type'], 'debug')
        self.assertIsNotNone(zero_entry['id'])
        self.assertIsNotNone(zero_entry['time'])

        #
        # Clear the scan results
        #
        response = requests.delete('%s/scans/%s' % (self.api_url, scan_id),
                                   auth=self.api_auth)
        self.assertEqual(response.json(), {u'message': u'Success'})

        return scan_id
