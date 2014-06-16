# coding: utf8
"""
test_export_requests.py

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
import urllib

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class TestExportRequests(PluginTest):

    target_url = get_moth_http('/grep/form_autocomplete/')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                ),
                'output': (
                    PluginConfig('export_requests',
                                 ('output_file',
                                  'output-fr.csv', PluginConfig.STR)),
                )
            }
        },
    }

    def test_export_requests(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        freq = self.kb.get_all_known_fuzzable_requests()

        self.assertTrue(os.path.exists('output-fr.csv'))
        file_urls = self._get_urls_from_file()

        self.assertEquals(
            set(sorted(file_urls)),
            set(sorted([fr.get_uri() for fr in freq]))
        )

    def _get_urls_from_file(self):
        # Get the contents of the output file
        for line in file('output-fr.csv'):
            if 'http' not in line:
                continue
            else:
                fr = FuzzableRequest.from_csv(line)
                yield fr.get_uri()

    def tearDown(self):
        super(TestExportRequests, self).tearDown()
        try:
            os.remove('output-fr.csv')
        except:
            pass