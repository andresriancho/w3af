'''
vuln.py

Copyright 2006 Andres Riancho

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
from core.data.kb.info import Info
from core.data.constants.severity import INFORMATION, LOW, MEDIUM, HIGH


class Vuln(Info):
    '''
    This class represents a web vulnerability.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self, name, desc, severity, response_ids,
                 plugin_name, data_obj=None):
        '''
        @param name: The vulnerability name, will be checked against the values
                     in core.data.constants.vulns.
        
        @param desc: The vulnerability description
        
        @param severity: The severity for this object
        
        @param response_ids: A list of response ids associated with this vuln
        
        @param plugin_name: The name of the plugin which identified the vuln
        
        @param data_obj: A Mutant or Vuln where we can take information from
                         and assign it to this object.
        '''
        Info.__init__(self, name, desc, response_ids, plugin_name,
                      data_obj)

        self.set_id(response_ids)
        self.set_name(name)
        self.set_desc(desc)
        self.set_severity(severity)
    
    def get_severity(self):
        return self._severity

    def set_severity(self, severity):
        if severity not in (INFORMATION, LOW, MEDIUM, HIGH):
            raise ValueError('Invalid severity value.')
        self._severity = severity

    def get_desc(self, with_id=True):
        return self._get_desc_impl('vulnerability', with_id)

    def __repr__(self):
        fmt = '<vuln object for vulnerability: "%s">'
        return fmt % self._desc
