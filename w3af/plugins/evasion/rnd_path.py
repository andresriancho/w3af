"""
rnd_path.py

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
import re

from w3af.core.controllers.plugins.evasion_plugin import EvasionPlugin
from w3af.core.data.fuzzer.utils import rand_alnum


class rnd_path(EvasionPlugin):
    """
    Add a random path to the URI.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def modify_request(self, request):
        """
        Mangles the request

        :param request: HTTPRequest instance that is going to be modified by
                        the evasion plugin
        :return: The modified request
        """
        # We mangle the URL
        path = request.url_object.get_path()
        if re.match('^/', path):
            random_alnum = rand_alnum()
            path = '/' + random_alnum + '/..' + path

        # Finally, we set all the mutants to the request in order to return it
        new_url = request.url_object.copy()
        new_url.set_path(path)

        # Finally, we set all the mutants to the request in order to return it
        new_req = request.copy()
        new_req.set_uri(new_url)

        return new_req

    def get_priority(self):
        """
        This function is called when sorting evasion plugins.
        Each evasion plugin should implement this.

        :return: An integer specifying the priority. 0 is run first, 100 last.
        """
        return 0

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This evasion plugin adds a random path to the URI.

        Example:
            Input:      '/bar/foo.asp'
            Output:     '/aflsasfasfkn/../bar/foo.asp'
        """
