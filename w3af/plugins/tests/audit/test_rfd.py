"""
test_rfd.py

Copyright 2012 Andres Riancho

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse

RUN_CONFIG = {
    'cfg': {
        'target': None,
        'plugins': {
            'audit': (PluginConfig('rfd'),),
            'crawl': (
                PluginConfig(
                    'web_spider',
                    ('only_forward', True, PluginConfig.BOOL)),
            )
        }
    }
}


class TestJSONAllFiltered(PluginTest):

    target_url = 'http://json-all-filtered/?q=rfd'

    MOCK_RESPONSES = [
              MockResponse(url='http://json-all-filtered/%3B/w3af.cmd%3B/'
                               'w3af.cmd?q=rfd',
                           body='message "w3afExecToken"',
                           content_type='text/json',
                           method='GET', status=200),
              MockResponse(url='http://json-all-filtered/%3B/w3af.cmd%3B/'
                               'w3af.cmd?q=w3afExecToken',
                           body='    {"a":"w3afExecToken","b":"b"}',
                           content_type='text/json',
                           method='GET', status=200),
              MockResponse(url='http://json-all-filtered/%3B/w3af.cmd%3B/'
                               'w3af.cmd?q=w3afExecToken%22%26%7C%0A',
                           body='    {"a":"w3afExecToken","b":"b"}',
                           content_type='application/javascript',
                           method='GET', status=200),
              ]

    def test_not_found_json_all_filtered(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('rfd', 'rfd')
        self.assertEquals(0, len(vulns))


class TestJSON(PluginTest):

    target_url = 'http://json/?q=rfd'

    MOCK_RESPONSES = [
              MockResponse(url='http://json/%3B/w3af.cmd%3B/w3af.cmd?q=rfd',
                           body='message "w3afExecToken"',
                           content_type='text/json',
                           method='GET', status=200),
              MockResponse(url='http://json/%3B/w3af.cmd%3B/w3af.cmd?'
                               'q=w3afExecToken',
                           body='    {"a":"w3afExecToken","b":"b"}',
                           content_type='text/json',
                           method='GET', status=200),
              MockResponse(url='http://json/%3B/w3af.cmd%3B/w3af.cmd?'
                               'q=w3afExecToken%22%26%7C%0A',
                           body='    {"a":"w3afExecToken"&|\n","b":"b"}',
                           content_type='application/javascript',
                           method='GET', status=200),
              ]

    def test_found_json(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('rfd', 'rfd')
        self.assertEquals(1, len(vulns))


class TestJSONDobleQuotesFiltered(PluginTest):

    target_url = 'http://json-filtered/?q=rfd'

    MOCK_RESPONSES = [
              MockResponse(url='http://json-filtered/%3B/w3af.cmd%3B/w3af.cmd?q=rfd',
                           body='message "w3afExecToken"',
                           content_type='text/json',
                           method='GET', status=200),
              MockResponse(url='http://json-filtered/%3B/w3af.cmd%3B/w3af.cmd?'
                               'q=w3afExecToken',
                           body='    {"a":"w3afExecToken","b":"b"}',
                           content_type='text/json',
                           method='GET', status=200),
              MockResponse(url='http://json-filtered/%3B/w3af.cmd%3B/w3af.cmd?'
                               'q=w3afExecToken%22%26%7C%0A',
                           body='    {"a":"w3afExecToken&|\n","b":"b"}',
                           content_type='application/javascript',
                           method='GET', status=200),
              ]

    def test_not_found_json(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('rfd', 'rfd')
        self.assertEquals(0, len(vulns))


class TestJSONP(PluginTest):

    target_url = 'http://jsonp/?callback=rfd'

    MOCK_RESPONSES = [
          MockResponse(url='http://jsonp/%3B/w3af.cmd%3B/w3af.cmd?callback'
                           '=rfd',
                       body='    rfd({ "Result": '
                            '{ "Timestamp": 1417601045 } }) ',
                       content_type='application/javascript',
                       method='GET', status=200),
          MockResponse(url='http://jsonp/%3B/w3af.cmd%3B/w3af.cmd?callback'
                           '=w3afExecToken',
                       body='    w3afExecToken({ "Result": '
                            '{ "Timestamp": 1417601045 } }) ',
                       content_type='application/javascript',
                       method='GET', status=200),
                      ]

    def test_found_jsonp(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('rfd', 'rfd')
        self.assertEquals(1, len(vulns))
