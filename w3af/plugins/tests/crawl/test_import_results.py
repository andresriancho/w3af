"""
test_import_results.py

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
import os

from nose.plugins.attrib import attr
from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest


class TestImportResults(PluginTest):

    base_url = 'http://moth/w3af/'

    BASE_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl',
                             'import_results')

    input_csv = os.path.join(BASE_PATH, 'input-test.csv')
    input_burp = os.path.join(BASE_PATH, 'input-nobase64.burp')
    input_burp_b64 = os.path.join(BASE_PATH, 'input-base64.burp')

    _run_configs = {
        'csv': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('import_results',
                                               ('input_csv', input_csv,
                                                PluginConfig.STR),
                                               ('input_burp', '', PluginConfig.STR)),)}
        },

        'burp64': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('import_results',
                                               ('input_csv',
                                                '', PluginConfig.STR),
                                               ('input_burp', input_burp_b64, PluginConfig.STR)),)}
        },

        'burp': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('import_results',
                                               ('input_csv',
                                                '', PluginConfig.STR),
                                               ('input_burp', input_burp, PluginConfig.STR)),)}
        },

    }

    @attr('ci_fails')
    def test_csv(self):
        """
        Note that the CSV file has the following tests in it:
            * Simple GET, no parameters, no QS
            * URL with HttP as protocol
            * GET with QS
            * POST with parameters
        """
        cfg = self._run_configs['csv']
        self._scan(cfg['target'], cfg['plugins'])

        fr_list = self.kb.get_all_known_fuzzable_requests()

        post_fr = [fr for fr in fr_list if isinstance(fr, HTTPPostDataRequest)]
        self.assertEqual(len(post_fr), 1)
        post_fr = post_fr[0]
        self.assertEqual(post_fr.get_url(
        ).url_string, 'http://moth/w3af/audit/xss/data_receptor.php')
        self.assertEqual(post_fr.get_dc(), {'firstname': ['abc']})
        self.assertEqual(post_fr.get_data(), 'firstname=abc')

        urls = [fr.get_uri().url_string for fr in fr_list if not isinstance(
            fr, HTTPPostDataRequest)]

        EXPECTED_URLS = set(
            ['http://moth/', 'http://moth/w3af/', 'http://moth/w3af/?id=1'])

        self.assertEqual(set(urls),
                         EXPECTED_URLS)

    @attr('ci_fails')
    def test_burp_b64(self):
        cfg = self._run_configs['burp64']
        self._scan(cfg['target'], cfg['plugins'])

        fr_list = self.kb.get_all_known_fuzzable_requests()

        post_fr = [fr for fr in fr_list if isinstance(fr, HTTPPostDataRequest)]
        self.assertEqual(len(post_fr), 1)
        post_fr = post_fr[0]
        self.assertEqual(post_fr.get_url(
        ).url_string, 'http://moth/w3af/audit/xss/data_receptor.php')
        self.assertEqual(
            post_fr.get_dc(), {u'user': [u'afsfasf'], u'firstname': [u'asf']})
        self.assertEqual(post_fr.get_data(), 'user=afsfasf&firstname=asf')

        urls = [fr.get_uri().url_string for fr in fr_list if not isinstance(
            fr, HTTPPostDataRequest)]

        EXPECTED_URLS = set(['http://moth/w3af/', 'http://moth/w3af/?id=1'])

        self.assertEqual(set(urls),
                         EXPECTED_URLS)

    @attr('ci_fails')
    def test_burp(self):
        cfg = self._run_configs['burp']
        self._scan(cfg['target'], cfg['plugins'])

        fr_list = self.kb.get_all_known_fuzzable_requests()

        post_fr = [fr for fr in fr_list if isinstance(fr, HTTPPostDataRequest)]
        self.assertEqual(len(post_fr), 1)
        post_fr = post_fr[0]
        self.assertEqual(post_fr.get_url(
        ).url_string, 'http://moth/w3af/audit/xss/data_receptor.php')
        self.assertEqual(
            post_fr.get_dc(), {u'user': [u'afsfasf'], u'firstname': [u'asf']})
        self.assertEqual(post_fr.get_data(), 'user=afsfasf&firstname=asf')

        urls = [fr.get_uri().url_string for fr in fr_list if not isinstance(
            fr, HTTPPostDataRequest)]

        EXPECTED_URLS = set(['http://moth/w3af/', 'http://moth/w3af/?id=1'])

        self.assertEqual(set(urls),
                         EXPECTED_URLS)