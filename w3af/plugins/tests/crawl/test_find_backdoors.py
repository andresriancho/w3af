"""
test_find_backdoor.py

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
import re

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.plugins.tests.constants.http_responses import get_apache_403


run_configs = {
    'base': {
        'target': None,
        'plugins': {'crawl': (PluginConfig('find_backdoors'),)}
    },
    'crawl': {
        'target': None,
        'plugins': {'crawl': (PluginConfig('find_backdoors'),
                              PluginConfig('web_spider'))}
    }
}


class TestFindBackdoor(PluginTest):
    domain = 'httpretty-mock'
    target_url = 'http://%s/' % domain

    MOCK_RESPONSES = [MockResponse('/', 'Hello world'),
                      MockResponse('/c99shell.php', 'cmd shell')]

    def test_find_backdoor(self):
        cfg = run_configs['base']
        self._scan(self.target_url, cfg['plugins'])

        vulns = self.kb.get('find_backdoors', 'backdoors')

        self.assertEqual(len(vulns), 1, vulns)

        vuln = vulns[0]

        vulnerable_url = self.target_url + 'c99shell.php'
        self.assertEqual(vuln.get_url().url_string, vulnerable_url)
        self.assertEqual(vuln.get_name(), 'Potential web backdoor')


class TestFalsePositiveFindBackdoor2017_1(PluginTest):
    """
    :see: https://github.com/andresriancho/w3af/issues/2017
    """
    domain = 'httpretty-mock'
    target_url = 'http://%s/' % domain

    APACHE_403 = get_apache_403('/foobar', domain)

    MOCK_RESPONSES = [MockResponse(re.compile('(.*)'), APACHE_403, status=403)]

    def test_2017_false_positive_backdoor(self):
        cfg = run_configs['base']
        self._scan(self.target_url, cfg['plugins'])

        vulns = self.kb.get('find_backdoors', 'backdoors')

        self.assertEqual(len(vulns), 0, vulns)


class TestFalsePositiveFindBackdoor2017_2(PluginTest):
    domain = 'httpretty-mock'
    target_url = 'http://%s/' % domain

    APACHE_403 = get_apache_403('/forbidden/foobar', domain)

    MOCK_RESPONSES = [MockResponse('/', '<a href="/forbidden/">403</a>'),
                      MockResponse('/forbidden/c99shell.php', 'cmd shell'),
                      MockResponse(re.compile('http://.*?/forbidden/.*'),
                                   APACHE_403, status=403)]

    def test_2017_false_positive_backdoor(self):
        cfg = run_configs['crawl']
        self._scan(self.target_url, cfg['plugins'])

        vulns = self.kb.get('find_backdoors', 'backdoors')

        self.assertEqual(len(vulns), 1, vulns)


class TestFalsePositiveFindBackdoorNixWizardEmail(PluginTest):
    target_url = 'http://httpretty-mock/'

    MOCK_RESPONSES = [MockResponse('/cmd.php', '<input name="cmd"/>')]

    def test_false_positive_backdoor(self):
        cfg = run_configs['crawl']
        self._scan(self.target_url, cfg['plugins'])

        vulns = self.kb.get('find_backdoors', 'backdoors')

        self.assertEqual(len(vulns), 1, vulns)


class TestFalsePositiveFindBackdoorNixWizardEmailNot(PluginTest):
    target_url = 'http://httpretty-mock/'

    MOCK_RESPONSES = [MockResponse('/cmd.php', '<input name="c1m2d"/>')]

    def test_false_positive_backdoor(self):
        cfg = run_configs['crawl']
        self._scan(self.target_url, cfg['plugins'])

        vulns = self.kb.get('find_backdoors', 'backdoors')

        self.assertEqual(len(vulns), 0, vulns)