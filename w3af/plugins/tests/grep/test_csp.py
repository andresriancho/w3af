"""
test_csp.py
 
Copyright 2013 Andres Riancho
 
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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig
 
 
class TestCSP(PluginTest):
 
    target_url = get_moth_http('/grep/csp/')

    _run_configs = {
        'cfg_with_error': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('csp'),),
                'crawl': (
                    PluginConfig('web_spider',
                    ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        },        
    }

    def test_found_vuln(self):
        """
        Test to validate case in which error are found:
        One vuln is common to several pages and others are isolated.
        """
        cfg = self._run_configs['cfg_with_error']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('csp', 'csp')

        EXPECTED = [#---This vuln is shared by several pages
                    "Directive 'default-src' allows all sources.",

                    #---These vulns are isolated
                    "Directive 'script-src' allows all javascript sources.",

                    "Directive 'script-src' is defined but no directive"
                    " 'script-nonce' is defined to protect javascript"
                    " resources.",

                    "Directive 'object-src' allows all plugin sources.",

                    "Some directives are misspelled: def-src, sript-src"]



        vuln_descs = set([v.get_desc(with_id=False) for v in vulns])
        self.assertEqual(set(EXPECTED), vuln_descs)
        self.assertAllVulnNamesEqual('CSP vulnerability', vulns)

        NOT_IN_FILENAME = 'csp_without_error.html'
        vuln_fnames = set([v.get_url().get_file_name() for v in vulns])
        self.assertNotIn(NOT_IN_FILENAME, vuln_fnames)
