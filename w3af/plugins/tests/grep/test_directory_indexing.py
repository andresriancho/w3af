"""
test_directory_indexing.py

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

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig

import w3af.core.data.constants.severity as severity


@attr('ci_ready')
class TestDirectoryIndexing(PluginTest):

    dir_indexing_url = get_moth_http('/grep/directory_indexing/index.html')

    _run_configs = {
        'cfg1': {
            'target': dir_indexing_url,
            'plugins': {
                'grep': (PluginConfig('directory_indexing'),)
            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        
        vulns = self.kb.get('directory_indexing', 'directory')
        self.assertEquals(1, len(vulns))
        v = vulns[0]
        
        self.assertEquals(self.dir_indexing_url, str(v.get_url()))
        self.assertEquals(severity.LOW, v.get_severity())
        self.assertEquals('Directory indexing',v.get_name())
