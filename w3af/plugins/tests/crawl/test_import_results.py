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

from w3af import ROOT_PATH
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.dc.multipart_container import MultipartContainer


class TestImportResults(PluginTest):

    base_url = get_moth_http()

    BASE_PATH = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl',
                             'import_results')

    input_base64 = os.path.join(BASE_PATH, 'w3af.base64')
    input_burp = os.path.join(BASE_PATH, 'burp-no-base64.xml')
    input_burp_b64 = os.path.join(BASE_PATH, 'burp-base64.xml')

    _run_configs = {
        'w3af': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('import_results',
                                               ('input_base64', input_base64,
                                                PluginConfig.STR),
                                               ('input_burp', '', PluginConfig.STR)),)}
        },

        'burp64': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('import_results',
                                               ('input_base64',
                                                '', PluginConfig.STR),
                                               ('input_burp', input_burp_b64, PluginConfig.STR)),)}
        },

        'burp': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('import_results',
                                               ('input_base64',
                                                '', PluginConfig.STR),
                                               ('input_burp', input_burp, PluginConfig.STR)),)}
        },

    }

    def test_base64(self):
        cfg = self._run_configs['w3af']
        self._scan(cfg['target'], cfg['plugins'])

        fuzzable_requests = self.kb.get_all_known_fuzzable_requests()

        #
        #   Assert that headers are loaded from the file
        #
        mozilla = 0
        for fuzzable_request in fuzzable_requests:
            user_agent, _ = fuzzable_request.get_headers().iget('user-agent')

            if user_agent is None:
                continue

            self.assertIn('mozilla', user_agent.lower())
            mozilla += 1

        self.assertGreater(mozilla, 0)

        #
        #   Assert that POST requests and their data are loaded from file
        #
        post_frs = [fr for fr in fuzzable_requests if fr.get_method() == 'POST']
        self.assertEqual(len(post_frs), 1)

        post_fr = post_frs[0]
        expected_post_url = 'http://127.0.0.1:8000/core/file_upload/upload.py'

        file_contents = 'Hello\nworld\n\nABC\n'

        self.assertEqual(post_fr.get_url().url_string, expected_post_url)
        self.assertEqual(post_fr.get_raw_data()['_file'][0], file_contents)

        #
        #   Assert that we found the URLs
        #
        urls = [fr.get_uri().url_string for fr in fuzzable_requests]

        expected_urls = {
            u'http://127.0.0.1:8000/',
            u'http://127.0.0.1:8000/static/moth/css/sticky-footer-navbar.css',
            u'http://127.0.0.1:8000/core/file_upload/upload.py',
            u'http://127.0.0.1:8000/static/moth/js/bootstrap.min.js',
            u'http://127.0.0.1:8000/static/moth/css/font-awesome/css/font-awesome.min.css',
            u'http://127.0.0.1:8000/static/moth/js/jquery.js',
            u'http://127.0.0.1:8000/static/moth/css/style.css',
            u'http://127.0.0.1:8000/about/',
            u'http://127.0.0.1:8000/static/moth/css/bootstrap.min.css',
            u'http://127.0.0.1:8000/w3af/file_upload/',
            u'http://127.0.0.1:8000/static/moth/images/w3af.png',
        }

        self.assertEqual(set(urls), expected_urls)

    def test_burp_b64(self):
        cfg = self._run_configs['burp64']
        self._scan(cfg['target'], cfg['plugins'])

        fuzzable_requests = self.kb.get_all_known_fuzzable_requests()

        #
        #   Assert that headers are loaded from the file
        #
        mozilla = 0
        for fuzzable_request in fuzzable_requests:
            user_agent, _ = fuzzable_request.get_headers().iget('user-agent')

            if user_agent is None:
                continue

            self.assertIn('mozilla', user_agent.lower())
            mozilla += 1

        self.assertGreater(mozilla, 0)

        #
        #   Assert that POST requests and their data are loaded from file
        #
        post_frs = [fr for fr in fuzzable_requests if fr.get_method() == 'POST']

        expected_post_urls = {'http://127.0.0.1:8000/audit/xss/simple_xss_form.py',
                              'http://127.0.0.1:8000/core/file_upload/upload.py'}
        post_urls = set([fr.get_uri().url_string for fr in post_frs])

        self.assertEqual(expected_post_urls, post_urls)

        expected_post_url = 'http://127.0.0.1:8000/core/file_upload/upload.py'
        file_contents = 'hello\nworld\n'

        post_fr = None

        for fr in fuzzable_requests:
            if fr.get_url().url_string.endswith('upload.py') and \
            isinstance(fr.get_raw_data(), MultipartContainer):
                post_fr = fr
                break

        self.assertEqual(post_fr.get_url().url_string, expected_post_url)
        self.assertIn('_file', post_fr.get_raw_data())
        self.assertEqual(post_fr.get_raw_data()['_file'][0], file_contents)

        #
        #   Assert that we found the URLs
        #
        urls = [fr.get_uri().url_string for fr in fuzzable_requests]

        expected_urls = {u'http://127.0.0.1:8000/',
                         u'http://127.0.0.1:8000/core/',
                         u'http://127.0.0.1:8000/favicon.ico',
                         u'http://127.0.0.1:8000/audit/xss/simple_xss_form.py',
                         u'http://127.0.0.1:8000/core/file_upload/upload.py',
                         u'http://127.0.0.1:8000/audit/',
                         u'http://127.0.0.1:8000/static/moth/css/font-awesome/fonts/fontawesome-webfont.woff?v=4.0.3'}

        self.assertEqual(set(urls), expected_urls)

    def test_burp(self):
        cfg = self._run_configs['burp']
        self._scan(cfg['target'], cfg['plugins'])

        fuzzable_requests = self.kb.get_all_known_fuzzable_requests()

        #
        #   Assert that headers are loaded from the file
        #
        mozilla = 0
        for fuzzable_request in fuzzable_requests:
            user_agent, _ = fuzzable_request.get_headers().iget('user-agent')

            if user_agent is None:
                continue

            self.assertIn('mozilla', user_agent.lower())
            mozilla += 1

        self.assertGreater(mozilla, 0)

        #
        #   Assert that POST requests and their data are loaded from file
        #
        post_frs = [fr for fr in fuzzable_requests if fr.get_method() == 'POST']

        expected_post_urls = {'http://127.0.0.1:8000/audit/xss/simple_xss_form.py',
                              'http://127.0.0.1:8000/core/file_upload/upload.py'}
        post_urls = set([fr.get_uri().url_string for fr in post_frs])

        self.assertEqual(expected_post_urls, post_urls)

        post_fr = None

        for fr in fuzzable_requests:
            if fr.get_url().url_string.endswith('upload.py') and \
            isinstance(fr.get_raw_data(), MultipartContainer):
                post_fr = fr
                break

        expected_post_url = 'http://127.0.0.1:8000/core/file_upload/upload.py'
        file_contents = 'hello\nworld\n'

        self.assertEqual(post_fr.get_url().url_string, expected_post_url)
        self.assertEqual(post_fr.get_raw_data()['_file'][0], file_contents)

        #
        #   Assert that we found the URLs
        #
        urls = [fr.get_uri().url_string for fr in fuzzable_requests]

        expected_urls = {u'http://127.0.0.1:8000/',
                         u'http://127.0.0.1:8000/core/',
                         u'http://127.0.0.1:8000/favicon.ico',
                         u'http://127.0.0.1:8000/audit/xss/simple_xss_form.py',
                         u'http://127.0.0.1:8000/core/file_upload/upload.py',
                         u'http://127.0.0.1:8000/audit/',
                         u'http://127.0.0.1:8000/static/moth/css/font-awesome/fonts/fontawesome-webfont.woff?v=4.0.3'}

        self.assertEqual(set(urls), expected_urls)
