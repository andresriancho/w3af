'''
test_xml_output.py

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
from lxml import etree

import core.data.kb.vuln as vuln

from core.data.parsers.urlParser import url_object
from ..helper import PluginTest, PluginConfig


class TestXMLOutput(PluginTest):
    
    xss_url = 'http://moth/w3af/audit/xss/'
    
    _run_configs = {
        'cfg': {
            'target': xss_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                         'xss',
                         ('checkStored', True, PluginConfig.BOOL),
                         ('numberOfChecks', 3, PluginConfig.INT)),
                    ),
                'discovery': (
                    PluginConfig(
                        'webSpider',
                        ('onlyForward', True, PluginConfig.BOOL)),
                ),
                'output': (
                    PluginConfig(
                        'xmlFile',
                        ('fileName', 'output-unittest.xml', PluginConfig.STR)),
                )         
            },
        }
    }
    
    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        xss_vulns = self.kb.getData('xss', 'xss')
        file_vulns = self._from_xml_get_vulns()
        
        self.assertEquals(
            set(sorted([v.getURL() for v in xss_vulns])),
            set(sorted([v.getURL() for v in file_vulns]))
        )
        
        self.assertEquals(
            set(sorted([v.getName() for v in xss_vulns])),
            set(sorted([v.getName() for v in file_vulns]))
        )
            
        self.assertEquals(
            set(sorted([v.getPluginName() for v in xss_vulns])),
            set(sorted([v.getPluginName() for v in file_vulns]))
        )

    def _from_xml_get_vulns(self):
        xp = XMLParser()
        parser = etree.XMLParser(target=xp)
        vulns = etree.fromstring(file('output-unittest.xml').read(), parser)
        return vulns
        
    def tearDown(self):
        super(TestXMLOutput, self).tearDown()
        try:
            os.remove('output-unittest.xml')
        except:
            pass

class XMLParser:
    vulns = []
    def start(self, tag, attrib):
        '''
        <vulnerability id="[87]" method="GET" name="Cross site scripting vulnerability" 
                       plugin="xss" severity="Medium" url="http://moth/w3af/audit/xss/simple_xss_no_script_2.php"
                       var="text">        
        '''        
        if tag == 'vulnerability':
            v = vuln.vuln()
            v.setPluginName(attrib['plugin'])
            v.setName(attrib['name'])
            v.setURL( url_object(attrib['url']) )
            self.vulns.append(v)
    
    def close(self):
        return self.vulns     
