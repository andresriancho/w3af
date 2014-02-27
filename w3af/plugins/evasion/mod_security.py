"""
mod_security.py

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
import urllib2
import copy

from w3af.core.controllers.plugins.evasion_plugin import EvasionPlugin

from w3af.core.data.parsers.url import parse_qs
from w3af.core.data.url.HTTPRequest import HTTPRequest as HTTPRequest


class mod_security(EvasionPlugin):
    """
    Evade detection using a mod_security vulnerability.

    :author: Francisco Amato ( famato |at| infobyte.com.ar )
    """

    def __init__(self):
        EvasionPlugin.__init__(self)

    def modify_request(self, request):
        """
        Mangles the request

        :param request: HTTPRequest instance that is going to be modified by
                        the evasion plugin
        :return: The modified request
        """
        # Mangle the postdata
        data = str(request.get_data())
        if data:

            try:
                # Only mangle the postdata if it is a url encoded string
                parse_qs(data)
            except:
                pass
            else:
                data = '\x00' + data
                headers_copy = copy.deepcopy(request.headers)
                headers_copy['content-length'] = str(len(data))

                request = HTTPRequest(request.url_object, data, headers_copy,
                                      request.get_origin_req_host())

        return request

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
        This evasion plugin performs a bypass for mod_security version 2.1.0 or less here:
            - http://www.php-security.org/MOPB/BONUS-12-2007.html

        Important: The evasion only works for postdata.

        Example:
            Post-data Input:      'a=b'
            Post-data Output :    '\\x00a=b'
        """
