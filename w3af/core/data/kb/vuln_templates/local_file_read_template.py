"""
local_file_reader_template.py

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


class LocalFileReadTemplate(BaseTemplate):
    """
    Vulnerability template for local file read vulnerability.
    """
    def __init__(self):
        super(LocalFileReadTemplate, self).__init__()
        
        self.name = self.get_vulnerability_name()
        self.payload = '/etc/passwd'
        self.file_pattern = 'root:x:0:0:'
        
    def get_options(self):
        ol = super(LocalFileReadTemplate, self).get_options()
        
        d = 'Payload used to detect the vulnerability (i.e. ../../etc/passwd)'
        o = opt_factory('payload', self.payload, d, 'string')
        ol.add(o)

        d = 'File pattern used to detect the vulnerability (i.e. root:x:0:0:)'
        o = opt_factory('file_pattern', self.file_pattern, d, 'string')
        ol.add(o)
        
        return ol
    
    def set_options(self, options_list):
        super(LocalFileReadTemplate, self).set_options(options_list)
        self.payload = options_list['payload'].get_value()
        self.file_pattern = options_list['file_pattern'].get_value()
    
    def create_vuln(self):
        v = super(LocalFileReadTemplate, self).create_vuln()

        v.get_mutant().set_token_value(self.payload)
        v['file_pattern'] = self.file_pattern

        return v
    
    def get_kb_location(self):
        """
        :return: A tuple with the location where the vulnerability will be
                 saved, example return value would be: ('lfi', 'lfi')
        """
        return 'lfi', 'lfi'

    def get_vulnerability_name(self):
        """
        :return: A string containing the name of the vulnerability to be added
                 to the KB, example: 'SQL Injection'. This is just a descriptive
                 string which can contain any information, not used for any
                 strict matching of vulns before exploiting.
        """
        return 'Arbitrary file read'

    def get_vulnerability_desc(self):
        return 'Arbitrary local file read vulnerability.'
