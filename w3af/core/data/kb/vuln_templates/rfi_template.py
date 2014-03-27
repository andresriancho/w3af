"""
rfi_template.py

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


class RFITemplate(BaseTemplate):
    """
    Vulnerability template for RFI vulnerability.
    """
    def __init__(self):
        super(RFITemplate, self).__init__()
        
        self.name = self.get_vulnerability_name()
        
    def get_kb_location(self):
        """
        :return: A tuple with the location where the vulnerability will be saved,
                 example return value would be: ('eval', 'eval')
        """
        return ('rfi', 'rfi')

    def get_vulnerability_name(self):
        """
        :return: A string containing the name of the vulnerability to be added
                 to the KB, example: 'SQL Injection'. This is just a descriptive
                 string which can contain any information, not used for any
                 strict matching of vulns before exploiting.
        """
        return 'Code execution via remote file inclusion'

    def get_vulnerability_desc(self):
        return 'Code execution vulnerability through remote file inclusion.'
