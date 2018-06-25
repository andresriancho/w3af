"""
test_find_dvcs.py

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

import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.plugins.crawl.find_dvcs import find_dvcs
from w3af.core.controllers.ci.w3af_moth import get_w3af_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestFindDVCS(PluginTest):

    base_url = get_w3af_moth_http('/w3af/crawl/find_dvcs/')

    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('find_dvcs'),
                                  PluginConfig('web_spider',
                                               ('only_forward', True, PluginConfig.BOOL)),)}
        }
    }

    # There are a couple commented-out repositories here because the test
    # environment doesn't fully support them yet, but the code for parsing
    # Git was tested in real life and works
    KNOWN_REPOS = (
        # 'git',
        'bzr',
        'hg',
        # 'svn',
        # 'cvs'
    )

    def test_dvcs(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        for repo in self.KNOWN_REPOS:

            vulns_for_repo = self.kb.get('find_dvcs', '%s repository' % repo)
            self.assertEqual(len(vulns_for_repo), 1, 'Failed at %s' % repo)

            vuln_repo = vulns_for_repo[0]

            expected_url_1 = self.base_url + repo
            expected_url_2 = self.base_url + '.' + repo

            url_start = (vuln_repo.get_url().url_string.startswith(expected_url_1) or
                         vuln_repo.get_url().url_string.startswith(expected_url_2))

            self.assertTrue(url_start, vuln_repo.get_url().url_string)

            self.assertEqual(vuln_repo.get_severity(), severity.MEDIUM)
            self.assertEqual(vuln_repo.get_name(), 'Source code repository')
            self.assertIn(repo, vuln_repo.get_desc().lower())

    def test_ignore_file_blank(self):
        fdvcs = find_dvcs()
        files = fdvcs.ignore_file('')

        self.assertEqual(files, set())

    def test_ignore_file_two_files_comment(self):
        fdvcs = find_dvcs()
        content = """# Ignore these files
        foo.txt
        bar*
        spam.eggs
        """
        files = fdvcs.ignore_file(content)

        self.assertEqual(files, {'foo.txt', 'spam.eggs'})


class TestSVN(PluginTest):

    WC_DB = file(os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl', 'find_dvcs', 'sample-wc.db')).read()

    SECRET = 'Secret contents here!'

    MOCK_RESPONSES = [MockResponse('http://mock/', 'root'),
                      MockResponse('http://mock/.svn/wc.db', WC_DB),
                      MockResponse('http://mock/.svn/pristine/96/96acedb8cc77c893b90d1ce37c7119fd0c0fba00.svn-base', SECRET),
                      MockResponse('http://mock/seris/changelog.rst', SECRET)]

    target_url = 'http://mock'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('find_dvcs'),
                                  PluginConfig('web_spider',
                                               ('only_forward', True, PluginConfig.BOOL)),)}
        }
    }

    def test_wc_db(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        url_list = kb.kb.get_all_known_urls()

        self.assertEqual({u.url_string for u in url_list},
                         {m.url for m in self.MOCK_RESPONSES})
