"""
wsdl_greper.py

Copyright 2006 Andres Riancho

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
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.esmre.multi_in import multi_in
from w3af.core.data.kb.info import Info


class wsdl_greper(GrepPlugin):
    """
    Grep every page for web service definition files.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    WSDL_STRINGS = ('xs:int', 'target_namespace', 'soap:body',
                    '/s:sequence', 'wsdl:', 'soapAction=',
                    # This isn't WSDL... but well...
                    'xmlns="urn:uddi"', '<p>Hi there, this is an AXIS service!</p>')
    _multi_in = multi_in(WSDL_STRINGS)

    def __init__(self):
        GrepPlugin.__init__(self)

        self._disco_strings = ['disco:discovery ']

    def grep(self, request, response):
        """
        Plugin entry point.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if response.get_code() == 200:
            self.analyze_wsdl(request, response)
            self.analyze_disco(request, response)
    
    def analyze_wsdl(self, request, response):
        match_list = self._multi_in.query(response.body)
        if len(match_list):
            desc = 'The URL: "%s" is a Web Services Description Language'\
                   ' page. This requires manual analysis to determine the'\
                   ' security of the web service.'
            desc = desc % response.get_url()
            
            i = Info('WSDL resource', desc, response.id,
                     self.get_name())
            i.set_url(response.get_url())
            i.add_to_highlight(*match_list)
            
            self.kb_append_uniq(self, 'wsdl', i, 'URL')

    def analyze_disco(self, request, response):
        for disco_string in self._disco_strings:
            if disco_string in response:
                desc = 'The URL: "%s" is a DISCO file that contains references'\
                       ' to WSDL URLs.'
                desc = desc % response.get_url()
                i = Info('DISCO resource', desc, response.id,
                         self.get_name())
                i.set_url(response.get_url())
                i.add_to_highlight(disco_string)
                
                self.kb_append_uniq(self, 'disco', i, 'URL')
                break
                
    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for WSDL definitions.

        Not all wsdls are found appending "?WSDL" to the url like crawl.wsdl_finder
        plugin does, this grep plugin will find some wsdl's that arent found by the
        crawl plugin.
        """
