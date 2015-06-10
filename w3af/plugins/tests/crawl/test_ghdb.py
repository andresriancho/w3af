"""
test_ghdb.py

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
import datetime

from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr
from mock import patch, call

import w3af.core.data.constants.severity as severity
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.crawl.ghdb import GoogleHack, google
from w3af.core.data.search_engines.google import GoogleResult
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.misc.file_utils import days_since_file_update


class TestGHDB(PluginTest):

    private_url = 'http://moth/'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'crawl': (PluginConfig('ghdb'),)}
        }
    }

    @attr('ci_fails')
    def test_ghdb_private(self):
        cfg = self._run_configs['cfg']

        with patch('w3af.plugins.crawl.web_diff.om.out') as om_mock:
            self._scan(self.private_url, cfg['plugins'])

            msg = 'There is no point in searching google for "site:moth".' \
                  ' Google doesn\'t index private pages.'

            self.assertIn(call.information(msg), om_mock.mock_calls)

        vulns = self.kb.get('ghdb', 'vuln')
        self.assertEqual(len(vulns), 0, vulns)

    @attr('ci_fails')
    def test_ghdb_match(self):

        call_count = 0

        def generate_google_result(*args):
            global call_count
            call_count += 1
            if call_count == 52:

                return [google_result, ]
            else:
                return []

        pmodule = 'w3af.plugins.crawl.ghdb.%s'
        with patch(pmodule % 'is_private_site') as private_site_mock:
            with patch.object(google, 'get_n_results') as google_mock_method:

                # Mock
                private_site_mock.return_value = False

                google_result = GoogleResult(
                    URL('http://moth/w3af/crawl/ghdb/'))
                google_mock_method.side_effect = [[], ] * 50 + [[google_result, ]] +\
                                                 [[], ] * 50000

                # Scan
                cfg = self._run_configs['cfg']
                self._scan(self.private_url, cfg['plugins'])

        # Assert
        vulns = self.kb.get('ghdb', 'vuln')
        self.assertEqual(len(vulns), 1, vulns)

        vuln = vulns[0]
        self.assertEqual(
            vuln.get_url().url_string, 'http://moth/w3af/crawl/ghdb/')
        self.assertEqual(vuln.get_severity(), severity.MEDIUM)
        self.assertEqual(vuln.get_name(), 'Google hack database match')

    def test_xml_parsing(self):
        ghdb_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'ghdb')

        ghdb_set = ghdb_inst._read_ghdb()

        self.assertGreater(len(ghdb_set), 300)

        for ghdb_inst in ghdb_set:
            self.assertIsInstance(ghdb_inst, GoogleHack)

    def test_too_old_xml(self):
        ghdb_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'ghdb')

        ghdb_file = ghdb_inst._ghdb_file
        is_older = days_since_file_update(ghdb_file, 30)

        msg = ('The GHDB database is too old, please update it by running the'
               ' following command:'
               '\n'
               '<secret wget-command>\n'
               'git commit -m "Update GHDB" w3af/plugins/crawl/ghdb/GHDB.xml\n'
               'git push\n'
               '\n'
               'Also remember to run this unittest again to verify that the'
               ' downloaded file can be parsed by the plugin.')
        self.assertFalse(is_older, msg)