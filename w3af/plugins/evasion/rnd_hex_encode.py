"""
rnd_hex_encode.py

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
from random import randint

from w3af.core.controllers.plugins.evasion_plugin import EvasionPlugin
from w3af.core.data.parsers.doc.url import parse_qs


class rnd_hex_encode(EvasionPlugin):
    """
    Add random hex encoding.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def modify_request(self, request):
        """
        Mangles the request

        :param request: HTTPRequest instance that is going to be modified
                        by the evasion plugin
        :return: The modified request
        """
        # First we mangle the URL
        path = request.url_object.get_path()
        path = self._mutate(path)

        # Finally, we set all the mutants to the request in order to return it
        new_url = request.url_object.copy()
        new_url.set_path(path)

        # Mangle the postdata
        data = request.get_data()
        if data:

            try:
                # Only mangle the postdata if it is a url encoded string
                parse_qs(data)
            except:
                pass
            else:
                data = self._mutate(data)

        new_req = request.copy()
        new_req.set_uri(new_url)
        new_req.set_data(data)

        return new_req

    def _mutate(self, data):
        """
        Replace some strings by it's hex encoded value.

        :return: a string.
        """
        new_data = ''

        for char in data:
            if char not in ['?', '/', '&', '\\', '=', '%', '+']:
                if randint(1, 2) == 2:
                    char = "%%%02x" % ord(char)
            new_data += char

        return new_data

    def get_priority(self):
        """
        This function is called when sorting evasion plugins.
        Each evasion plugin should implement this.

        :return: An integer specifying the priority. 0 is run first, 100 last.
        """
        return 50

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This evasion plugin adds random hex encoding.

        Example:
            Input:      '/bar/foo.asp'
            Output:     '/b%61r/%66oo.asp'
        """
