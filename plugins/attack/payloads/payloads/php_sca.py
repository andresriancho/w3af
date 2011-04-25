'''
php_sca.py

Copyright 2011 Andres Riancho

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

import tempfile

from core.controllers.sca.sca import PhpSCA
from core.data.dc.dataContainer import dataContainer as dataContainer
from core.ui.consoleUi.tables import table
from plugins.attack.payloads.base_payload import base_payload
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln


class php_sca(base_payload):
    
    KB_DATA = {
        'XSS': {'kb_key': ('xss', 'xss'), 'severity': severity.MEDIUM,
            'name': 'Cross site scripting vulnerability'},
        'OS_COMMANDING': {'kb_key': ('osCommanding', 'osCommanding'),
            'severity': severity.HIGH, 'name': 'OS commanding vulnerability'},
        'FILE_INCLUDE': {'kb_key': ('localFileInclude', 'localFileInclude'),
            'severity': severity.MEDIUM, 'name': 'Local file inclusion vulnerability'},
       }
    
    def api_read(self, localtmpdir=None):
        '''
        @param localtmpdir: Local temporary directory where to save
            the remote code.
        '''
        
        def write_vuln_to_kb(vulnty, url, funcs):
            vulndata = php_sca.KB_DATA[vulnty]
            for f in funcs:
                v = vuln.vuln()
                v.setSeverity(vulndata['severity'])
                v.setName(vulndata['name'])
                v.setURL(url)
                v.setURI(url)
                v.setVar(f.vulnsources[0])
                v.setDesc(vulndata['name'])
                args = list(vulndata['kb_key']) + [v]

                # TODO: Extract the method from the PHP code
                #     $_GET == GET
                #     $_POST == POST
                #     $_REQUEST == GET
                v.setMethod('GET')
                
                # TODO: Extract all the other variables that are
                # present in the PHP file using the SCA
                v.setDc(dataContainer())
                
                #
                ## TODO: This needs to be checked! OS Commanding specific
                ### parameters
                v['os'] = 'unix'
                v['separator'] = ''
                ###
                ##
                #
                kb.kb.append(*args)
        
        if not localtmpdir:
            localtmpdir = tempfile.mkdtemp()
        
        res = {}
        files = self.exec_payload('get_source_code', (localtmpdir,))
        
        for url, file in files.iteritems():
            sca = PhpSCA(file=file[1])
            for vulnty, funcs in sca.get_vulns().iteritems():
                # Write to KB
                write_vuln_to_kb(vulnty, url, funcs)
                # Fill res dict
                res.setdefault(vulnty, []).extend(
                    [{'loc': url, 'lineno': fc.lineno, 'funcname': fc.name,
                      'vulnsrc': str(fc.vulnsources[0])} for fc in funcs])
        return res
        
    
    def run_read(self, parameters):

        api_res = self.api_read()
        if not api_res:
            return 'No vulnerability was found.'
        
        rows = [['Vuln Type', 'Remote Location', 'Vuln Param', 'Lineno'], []]
        for vulnty, files in api_res.iteritems():
            for f in files:
                rows.append([vulnty, f['loc'], f['vulnsrc'], str(f['lineno'])])
        
        restable = table(rows)
        restable.draw(100)
