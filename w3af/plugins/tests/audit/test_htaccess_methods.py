"""
test_htaccess_methods.py

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
            'audit': (PluginConfig('htaccess_methods'),),
            'crawl': (
                PluginConfig(
                    'web_spider',
                    ('only_forward', True, PluginConfig.BOOL)),
            )
        }
    }
}


class TestHTAccess(PluginTest):

    target_url = 'http://mock/'

    MOCK_RESPONSES = [MockResponse(target_url, 'Bad credentials',
                                   method='GET', status=401),
                      MockResponse(target_url, 'Hidden treasure', method='POST',
                                   status=200)]

    def test_found_htaccess_methods(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('htaccess_methods', 'auth')

        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Misconfigured access control', vuln.get_name())
        self.assertEquals(self.target_url, str(vuln.get_url()))


class TestHTAccessFalsePositiveGeneric(PluginTest):

    target_url = 'http://mock/'

    MOCK_RESPONSES = [MockResponse(target_url, 'Bad credentials',
                                   method='GET', status=401),
                      MockResponse(target_url, 'Bad credentials',
                                   method='POST', status=403)]

    def test_false_positive(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('htaccess_methods', 'auth')

        self.assertEquals(0, len(vulns))


class TestHTaccessCheck1915_1(TestHTAccessFalsePositiveGeneric):
    # https://github.com/andresriancho/w3af/issues/1915
    MOCK_RESPONSES = [MockResponse(TestHTAccessFalsePositiveGeneric.target_url,
                                   'Bad credentials', method='GET', status=401)]


class TestHTaccessCheck1915_2(TestHTAccessFalsePositiveGeneric):
    # https://github.com/andresriancho/w3af/issues/1915
    MOCK_RESPONSES = [MockResponse(TestHTAccessFalsePositiveGeneric.target_url,
                                   'Bad credentials', method='GET', status=401),
                      MockResponse(TestHTAccessFalsePositiveGeneric.target_url,
                                   'Bad credentials', method='POST', status=401)]
