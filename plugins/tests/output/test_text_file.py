'''
test_text_file.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
'''
import os
import re

from nose.plugins.attrib import attr

import core.data.kb.vuln as vuln

from core.data.parsers.url import URL
from ..helper import PluginTest, PluginConfig


@attr('smoke')
class TestTextFile(PluginTest):
    
    OUTPUT_FILE = 'output-unittest.txt'
    
    target_url = 'http://moth/w3af/audit/sql_injection/select/sql_injection_string.php'
    
    _run_configs = {
        'cfg': {
            'target': target_url + '?name=xxx',
            'plugins': {
                'audit': (PluginConfig('sqli'),),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('onlyForward', True, PluginConfig.BOOL)),
                ),
                'output': (
                    PluginConfig(
                        'text_file',
                        ('fileName', OUTPUT_FILE, PluginConfig.STR)),
                )         
            },
        }
    }
    
    def test_found_vulns(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        kb_vulns = self.kb.get('sqli', 'sqli')
        file_vulns = self._from_txt_get_vulns()
        
        self.assertEqual(len(kb_vulns), 1, kb_vulns)
        
        self.assertEquals(
            set(sorted([v.getURL() for v in kb_vulns])),
            set(sorted([v.getURL() for v in file_vulns]))
        )
        
        self.assertEquals(
            set(sorted([v.get_method() for v in kb_vulns])),
            set(sorted([v.get_method() for v in file_vulns]))
        )

    def _from_txt_get_vulns(self):
        file_vulns = []
        vuln_regex = 'SQL injection in a .*? was found at: "(.*?)"' \
                     ', using HTTP method (.*?). The sent .*?data was: "(.*?)"'
        vuln_re = re.compile(vuln_regex)

        for line in file(self.OUTPUT_FILE):
            mo = vuln_re.search(line)

            if mo:
                v = vuln.vuln()
                v.setURL( URL(mo.group(1)) )
                v.setMethod( mo.group(2) )
                file_vulns.append(v)
        
        return file_vulns
            
    def tearDown(self):
        try:
            os.remove(self.OUTPUT_FILE)
        except:
            pass
