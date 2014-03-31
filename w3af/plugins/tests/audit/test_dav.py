"""
test_dav.py

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

from nose.plugins.attrib import attr
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestDav(PluginTest):

    target_vuln_all = 'http://moth/w3af/audit/dav/write-all/'
    target_no_privs = 'http://moth/w3af/audit/dav/no-privileges/'
    target_safe_all = 'http://moth/w3af/audit/eval/'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                'audit': (PluginConfig('dav',),),
            }
        },
    }

    @attr('ci_fails')
    def test_found_all_dav(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_vuln_all, cfg['plugins'])

        vulns = self.kb.get('dav', 'dav')

        EXPECTED_NAMES = set(['Insecure DAV configuration'] * 2)

        self.assertEquals(EXPECTED_NAMES,
                          set([v.get_name() for v in vulns])
                          )

        self.assertEquals(set(['PUT', 'PROPFIND']),
                          set([v.get_method() for v in vulns]))

        self.assertTrue(all([self.target_vuln_all == str(
            v.get_url().get_domain_path()) for v in vulns]))

    @attr('ci_fails')
    def test_no_privileges(self):
        """
        DAV is configured but the directory doesn't have the file-system permissions
        to allow the Apache process to write to it.
        """
        cfg = self._run_configs['cfg']
        self._scan(self.target_no_privs, cfg['plugins'])

        vulns = self.kb.get('dav', 'dav')

        self.assertEquals(len(vulns), 2, vulns)

        iname = 'DAV incorrect configuration'
        info_no_privs = [i for i in vulns if i.get_name() == iname][0]

        vname = 'Insecure DAV configuration'
        vuln_propfind = [v for v in vulns if v.get_name() == vname][0]
         
        info_url =  str(info_no_privs.get_url().get_domain_path())
        vuln_url =  str(vuln_propfind.get_url().get_domain_path())
        
        self.assertEquals(self.target_no_privs, info_url)
        self.assertEquals(self.target_no_privs, vuln_url)

    @attr('ci_fails')
    def test_not_found_dav(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_safe_all, cfg['plugins'])

        vulns = self.kb.get('dav', 'dav')
        self.assertEquals(0, len(vulns))