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
from threading import RLock

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.data.url.helpers import is_no_content_response
from w3af.core.data.kb.info import Info


class server_header(InfrastructurePlugin):
    """
    Identify the server type based on the server header.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._server_headers = set()
        self._x_powered = set()
        self._lock = RLock()

    def discover(self, fuzzable_request, debugging_id):
        """
        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        """
        response = self._uri_opener.GET(fuzzable_request.get_url(), cache=True)

        with self._lock:
            self._check_server_header(fuzzable_request, response)
            self._check_x_power(fuzzable_request, response)

    def _check_server_header(self, fuzzable_request, response):
        """
        HTTP GET and analyze response for server header
        """
        if is_no_content_response(response):
            #
            # UrlOpenerProxy(), a helper class used by most plugins, will
            # generate 204 HTTP responses for HTTP requests that fail.
            # This makes plugins have less error handling code (try/except),
            # and looks like this in the scan log:
            #
            #   Generated 204 "No Content" response (id:2131)
            #
            # The problem is that in some strange cases, like this plugin,
            # the 204 response will trigger a false positive. Because of
            # that I had to add this if statement to completely ignore
            # the HTTP responses with 204 status code
            #
            return

        server, header_name = response.get_headers().iget('server')

        if server in self._server_headers:
            return

        self._server_headers.add(server)

        if server:
            desc = 'The server header for the remote web server is: "%s".'
            desc %= server

            i = Info('Server header', desc, response.id, self.get_name())
            i['server'] = server
            i.add_to_highlight(header_name + ':')

            om.out.information(i.get_desc())

            # Save the results in the KB so the user can look at it
            kb.kb.append(self, 'server', i)

            # Also save this for easy internal use
            # other plugins can use this information
            kb.kb.raw_write(self, 'server_string', server)
        else:
            # strange !
            desc = ('The remote HTTP Server omitted the "server" header in'
                    ' its response.')
            i = Info('Omitted server header', desc, response.id,
                     self.get_name())

            om.out.information(i.get_desc())

            # Save the results in the KB so that other plugins can use this
            # information
            kb.kb.append(self, 'omitted_server_header', i)

            # Also save this for easy internal use
            # other plugins can use this information
            kb.kb.raw_write(self, 'server_string', '')

    def _check_x_power(self, fuzzable_request, response):
        """
        Analyze X-Powered-By header.
        """
        for header_name in response.get_headers().keys():
            for needle in ['ASPNET', 'POWERED']:
                if needle in header_name.upper():
                    powered_by = response.get_headers()[header_name]

                    if powered_by in self._x_powered:
                        return

                    self._x_powered.add(powered_by)

                    desc = 'The %s header for the target HTTP server is "%s".'
                    desc %= (header_name, powered_by)

                    i = Info('Powered-by header', desc, response.id, self.get_name())
                    i['powered_by'] = powered_by
                    i.add_to_highlight(header_name + ':')

                    om.out.information(i.get_desc())

                    # Save the results in the KB so that other plugins can
                    # use this information. Before knowing that some servers
                    # may return more than one poweredby header I had:
                    #
                    #     kb.kb.raw_write( self , 'powered_by' , powered_by )
                    #
                    # But I have seen an IIS server with PHP that returns
                    # both the ASP.NET and the PHP headers
                    kb.kb.append(self, 'powered_by', i)

                    # Save the list to the KB
                    kb.kb.raw_write(self, 'powered_by_string', list(powered_by))

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin GETs the server header and saves the result to the
        knowledge base.

        Nothing strange, just do a GET request to the url and save the server
        headers to the kb. A smarter way to check the server type is with the
        hmap plugin.
        """
