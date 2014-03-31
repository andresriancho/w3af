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
import w3af.core.data.constants.severity as severity

from nose.plugins.attrib import attr
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.crawl.find_dvcs import find_dvcs


class TestFindDVCS(PluginTest):

    base_url = 'http://moth/w3af/crawl/find_dvcs/'

    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('find_dvcs'),
                                  PluginConfig('web_spider',
                                               ('only_forward', True, PluginConfig.BOOL)),)}
        }
    }

    @attr('ci_fails')
    def test_dvcs(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        vulns_git = self.kb.get('find_dvcs', 'git repository')
        vulns_bzr = self.kb.get('find_dvcs', 'bzr repository')
        vulns_hg = self.kb.get('find_dvcs', 'hg repository')
        vulns_svn = self.kb.get('find_dvcs', 'svn repository')
        vulns_cvs = self.kb.get('find_dvcs', 'cvs repository')

        self.assertEqual(len(vulns_git), 1, vulns_git)
        self.assertEqual(len(vulns_bzr), 1, vulns_bzr)
        self.assertEqual(len(vulns_hg), 1, vulns_hg)
        #FIXME: What to do about dups?
        self.assertTrue(len(vulns_svn) > 0, vulns_svn)
        self.assertTrue(len(vulns_cvs) > 0, vulns_cvs)

        for repo in ('git', 'bzr', 'hg', 'svn', 'cvs'):

            vuln_repo = self.kb.get('find_dvcs', repo + ' repository')[0]

            expected_url_1 = self.base_url + repo
            expected_url_2 = self.base_url + '.' + repo
            url_start = vuln_repo.get_url().url_string.startswith(expected_url_1) or \
                vuln_repo.get_url(
                ).url_string.startswith(expected_url_2)

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

        self.assertEqual(files, set(['foo.txt', 'spam.eggs']))