'''
server_header.py

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
import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
from core.data.kb.info import Info

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin


class server_header(InfrastructurePlugin):
    '''
    Identify the server type based on the server header.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._server_header = True
        self._x_powered = True

    def discover(self, fuzzable_request):
        '''
        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.

        @param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        '''
        if self._server_header:
            self._server_header = False
            self._check_server_header(fuzzable_request)

        if self._x_powered:
            self._check_x_power(fuzzable_request)

    def _check_server_header(self, fuzzable_request):
        '''
        HTTP GET and analyze response for server header
        '''
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)

        for hname, hvalue in response.get_lower_case_headers().iteritems():
            if hname == 'server':
                server = hvalue
                i = Info()
                i.set_plugin_name(self.get_name())
                i.set_name('Server header')
                i.set_id(response.get_id())
                i.set_desc('The server header for the remote web server is: "' + server + '".')
                i['server'] = server
                om.out.information(i.get_desc())
                i.add_to_highlight(hname + ':')

                # Save the results in the KB so the user can look at it
                kb.kb.append(self, 'server', i)

                # Also save this for easy internal use
                # other plugins can use this information
                kb.kb.save(self, 'serverString', server)
                break

        else:
            # strange !
            i = Info()
            i.set_plugin_name(self.get_name())
            i.set_name('Omitted server header')
            i.set_id(response.get_id())
            msg = 'The remote HTTP Server omitted the "server" header in its response.'
            i.set_desc(msg)
            om.out.information(i.get_desc())

            # Save the results in the KB so that other plugins can use this
            # information
            kb.kb.append(self, 'omittedHeaders', i)

            # Also save this for easy internal use
            # other plugins can use this information
            kb.kb.save(self, 'serverString', '')

    def _check_x_power(self, fuzzable_request):
        '''
        Analyze X-Powered-By header.
        '''
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
                    pow_by_kb = kb.kb.get('server_header', 'poweredBy')
                    powered_by_in_kb = [j['poweredBy'] for j in pow_by_kb]
                    if powered_by not in powered_by_in_kb:

                        #
                        #    I don't have it in the KB, so I need to add it,
                        #
                        i = Info()
                        i.set_plugin_name(self.get_name())
                        i.set_name('"%s" header' % header_name)
                        i.set_id(response.get_id())
                        msg = '"' + header_name + \
                            '" header for this HTTP server is: "'
                        msg += powered_by + '".'
                        i.set_desc(msg)
                        i['poweredBy'] = powered_by
                        om.out.information(i.get_desc())
                        i.add_to_highlight(header_name + ':')

                        # Save the results in the KB so that other plugins can
                        # use this information. Before knowing that some servers
                        # may return more than one poweredby header I had:
                        #     kb.kb.save( self , 'poweredBy' , poweredBy )
                        # But I have seen an IIS server with PHP that returns
                        # both the ASP.NET and the PHP headers
                        pow_by_kb = kb.kb.get('server_header', 'poweredBy')
                        powered_by_in_kb = [j['poweredBy'] for j in pow_by_kb]

                        if powered_by not in powered_by_in_kb:
                            kb.kb.append(self, 'poweredBy', i)
                            kb.kb.append(
                                self, 'poweredByString', powered_by)

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin GETs the server header and saves the result to the knowledge base.

        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.
        '''
