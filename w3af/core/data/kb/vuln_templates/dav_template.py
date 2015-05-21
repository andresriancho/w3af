"""
dav_template.py

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
from w3af.core.data.kb.vuln_templates.base_template import BaseTemplate
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL


class DAVTemplate(BaseTemplate):
    """
    Vulnerability template for DAV vulnerability.
    """
    def __init__(self):
        super(DAVTemplate, self).__init__()
        
        self.name = self.get_vulnerability_name()
        self.url = URL('http://host.tld/')

    def get_options(self):
        """
        In this case we provide a sample implementation since most
        vulnerabilities will have this template. If the specific vulnerability
        needs other params then it should override this implementation.
        """
        ol = OptionList()

        d = 'Vulnerability name (eg. %s)' % self.get_vulnerability_name()
        o = opt_factory('name', self.name, d, 'string')
        ol.add(o)

        d = 'URL pointing to the path that is vulnerable to file uploads via'\
            ' misconfigured DAV module (HTTP PUT method).'
        o = opt_factory('url', self.url, d, 'url')
        ol.add(o)

        return ol

    def set_options(self, options_list):
        self.name = options_list['name'].get_value()
        self.url = options_list['url'].get_value()

    def create_vuln(self):
        v = self.create_base_vuln()

        # User configured
        v.set_name(self.name)
        v.set_url(self.url)

        return v

    def get_kb_location(self):
        """
        :return: A tuple with the location where the vulnerability will be saved,
                 example return value would be: ('eval', 'eval')
        """
        return 'dav', 'dav'

    def get_vulnerability_name(self):
        """
        :return: A string containing the name of the vulnerability to be added
                 to the KB, example: 'SQL Injection'. This is just a descriptive
                 string which can contain any information, not used for any
                 strict matching of vulns before exploiting.
        """
        return 'DAV Misconfiguration'

    def get_vulnerability_desc(self):
        return 'DAV misconfiguration which allows file uploads using the HTTP'\
               ' PUT method'
