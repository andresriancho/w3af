"""
rnd_param.py

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
import copy

from w3af.core.controllers.plugins.evasion_plugin import EvasionPlugin
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.parsers.doc.url import parse_qs


class rnd_param(EvasionPlugin):
    """
    Add a random parameter.
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
        qs = copy.deepcopy(request.url_object.querystring)
        qs = self._mutate(qs)

        # Finally, we set all the mutants to the request in order to return it
        new_url = request.url_object.copy()
        new_url.querystring = qs

        # Mangle the postdata
        data = request.get_data()
        if data:
            try:
                # Only mangle the postdata if it is a url encoded string
                post_data = parse_qs(data)
            except:
                pass
            else:
                data = str(self._mutate(post_data))

        new_req = request.copy()
        new_req.set_uri(new_url)
        new_req.set_data(data)

        return new_req

    def _mutate(self, data):
        """
        Add a random parameter.

        :param data: A dict-like object.
        :return: The same object with one new key-value.
        """
        key = rand_alnum(5)
        value = rand_alnum(8)
        data[key] = [value]
        return data

    def get_priority(self):
        """
        This function is called when sorting evasion plugins.
        Each evasion plugin should implement this.

        :return: An integer specifying the priority. 100 is run first, 0 last.
        """
        return 50

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This evasion plugin adds a random parameter.

        Example:
            Input:      '/bar/foo.asp'
            Output:     '/bar/foo.asp?alsfkj=f09'
        """
