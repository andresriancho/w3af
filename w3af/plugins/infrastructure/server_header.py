"""
server_header.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.data.kb.info import Info


class server_header(InfrastructurePlugin):
    """
    Identify the server type based on the server header.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._server_header = True
        self._x_powered = True

    def discover(self, fuzzable_request):
        """
        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.

        :param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        """
        if self._server_header:
            self._server_header = False
            self._check_server_header(fuzzable_request)

        if self._x_powered:
            self._check_x_power(fuzzable_request)

    def _check_server_header(self, fuzzable_request):
        """
        HTTP GET and analyze response for server header
        """
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)

        for hname, hvalue in response.get_lower_case_headers().iteritems():
            if hname == 'server':
                server = hvalue
                
                desc = 'The server header for the remote web server is: "%s".'
                desc = desc % server
                
                i = Info('Server header', desc, response.id, self.get_name())
                i['server'] = server
                i.add_to_highlight(hname + ':')
                
                om.out.information(i.get_desc())

                # Save the results in the KB so the user can look at it
                kb.kb.append(self, 'server', i)

                # Also save this for easy internal use
                # other plugins can use this information
                kb.kb.raw_write(self, 'server_string', server)
                break

        else:
            # strange !
            desc = 'The remote HTTP Server omitted the "server" header in'\
                  ' its response.'
            i = Info('Omitted server header', desc, response.id,
                     self.get_name())

            om.out.information(i.get_desc())

            # Save the results in the KB so that other plugins can use this
            # information
            kb.kb.append(self, 'ommited_server_header', i)

            # Also save this for easy internal use
            # other plugins can use this information
            kb.kb.raw_write(self, 'server_string', '')

    def _check_x_power(self, fuzzable_request):
        """
        Analyze X-Powered-By header.
        """
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)

        for header_name in response.get_headers().keys():
            for i in ['ASPNET', 'POWERED']:
                if i in header_name.upper() or header_name.upper() in i:
                    powered_by = response.get_headers()[header_name]

                    # Only get the first one
                    self._x_powered = False

                    #
                    #    Check if I already have this info in the KB
                    #
                    pow_by_kb = kb.kb.get('server_header', 'powered_by')
                    powered_by_in_kb = [j['powered_by'] for j in pow_by_kb]
                    if powered_by not in powered_by_in_kb:

                        #
                        #    I don't have it in the KB, so I need to add it,
                        #
                        desc = 'The %s header for the target HTTP server is "%s".'
                        desc = desc % (header_name, powered_by)
                        
                        i = Info('Powered-by header', desc, response.id,
                                 self.get_name())
                        i['powered_by'] = powered_by
                        i.add_to_highlight(header_name + ':')
                        
                        om.out.information(i.get_desc())

                        # Save the results in the KB so that other plugins can
                        # use this information. Before knowing that some servers
                        # may return more than one poweredby header I had:
                        #     kb.kb.raw_write( self , 'powered_by' , powered_by )
                        # But I have seen an IIS server with PHP that returns
                        # both the ASP.NET and the PHP headers
                        kb.kb.append(self, 'powered_by', i)
                        
                        # Update the list and save it,
                        powered_by_in_kb.append(powered_by)
                        kb.kb.raw_write(self, 'powered_by_string',
                                        powered_by_in_kb)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin GETs the server header and saves the result to the knowledge base.

        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.
        """
