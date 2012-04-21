'''
test_form_autocomplete.py

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

from ..helper import PluginTest, PluginConfig
import core.data.constants.severity as severity

class TestFormAutocomplete(PluginTest):
    
    target_url = 'http://moth/w3af/grep/form_autocomplete/'
    
    _run_configs = {
        'cfg1': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('formAutocomplete'),),
                'discovery': (
                    PluginConfig('webSpider',
                             ('onlyForward', True, PluginConfig.BOOL)),
                )         
            }
        }
    }
    
    def test_found_vuln(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.getData('formAutocomplete', 'formAutocomplete')
        
        expected_results = [ "index-form-default.html",
                             "index-form-on.html",
                             "index-form-on-field-on.html"]

        self.assertEquals(3, len(vulns))
        
        filenames = [vuln.getURL().getFileName() for vuln in vulns]
        filenames.sort()
        expected_results.sort()
        
        self.assertEquals(expected_results, filenames)

