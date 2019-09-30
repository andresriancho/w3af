"""
ms15_034.py

Copyright 2015 Andres Riancho

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
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.vuln import Vuln


class ms15_034(InfrastructurePlugin):
    """
    Detect MS15-034 - Remote code execution in HTTP.sys

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Checks if the remote IIS is vulnerable to MS15-034

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        url = fuzzable_request.get_url()
        headers = Headers([('Range', 'bytes=18-18446744073709551615')])

        response = self._uri_opener.GET(url,
                                        cache=False,
                                        grep=False,
                                        headers=headers)

        if response.get_code() == 416:
            desc = ('The target IIS web server is vulnerable to MS15-034 which'
                    ' allows remote code execution due to a flaw in HTTP.sys')

            v = Vuln('MS15-034', desc, severity.HIGH, response.id,
                     self.get_name())
            v.set_url(response.get_url())

            self.kb_append_uniq(self, 'ms15_034', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Checks if the remote IIS is vulnerable to MS15-034 by sending one HTTP
        request containing the `Range: bytes=18-18446744073709551615` header.

        Warning: In some strange scenarios this test can cause a Denial of
        Service.
        """

