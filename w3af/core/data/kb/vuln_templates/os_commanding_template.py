"""
os_commanding_template.py

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
from w3af.core.data.kb.vuln_templates.base_template import BaseTemplate
from w3af.core.data.options.opt_factory import opt_factory


class OSCommandingTemplate(BaseTemplate):
    """
    Vulnerability template for eval vulnerability.
    """
    def __init__(self):
        super(OSCommandingTemplate, self).__init__()
        
        self.name = self.get_vulnerability_name()
        self.operating_system = 'linux'
        self.separator = '&'
        
    def get_options(self):
        ol = super(OSCommandingTemplate, self).get_options()
        
        d = 'Command separator used for injecting commands. Usually one of'\
            '&, |, &&, || or ; .'
        o = opt_factory('separator', self.separator, d, 'string')
        ol.add(o)

        d = 'Remote operating system (linux or windows).'
        o = opt_factory('operating_system', self.operating_system, d, 'string')
        ol.add(o)
        
        return ol
    
    def set_options(self, options_list):
        super(OSCommandingTemplate, self).set_options(options_list)
        self.separator = options_list['separator'].get_value()
        self.operating_system = options_list['operating_system'].get_value()
    
    def create_vuln(self):
        v = super(OSCommandingTemplate, self).create_vuln()
        
        v['separator'] = self.separator
        v['os'] = self.operating_system
        
        return v
        
    def get_kb_location(self):
        """
        :return: A tuple with the location where the vulnerability will be
                 saved, example return value would be: ('eval', 'eval')
        """
        return 'os_commanding', 'os_commanding'

    def get_vulnerability_name(self):
        """
        :return: A string containing the name of the vulnerability to be added
                 to the KB, example: 'SQL Injection'. This is just a descriptive
                 string which can contain any information, not used for any
                 strict matching of vulns before exploiting.
        """
        return 'OS Commanding code execution'

    def get_vulnerability_desc(self):
        return 'Code execution vulnerability through injection of operating'\
               ' system commands.'
