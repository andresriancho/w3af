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
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.data.parsers import parser_cache
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.vuln import Vuln


class ms15_034(InfrastructurePlugin):
    """
    Detect MS15-034 - Remote code execution in HTTP.sys

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request):
        """
        Checks if the remote IIS is vulnerable to MS15-034

        Request image files for better detection
        """

        image_urls = self._get_images(fuzzable_request)

        for url in image_urls:

            headers = Headers([('Range', 'bytes=0-18446744073709551615')])

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

                break

    def _get_images(self, fuzzable_request):
        """
        Get all img tags and retrieve the src list.

        :param fuzzable_request: The request to modify
        :return: A list with containing image sources
        """
        res = []

        try:
            response = self._uri_opener.GET(fuzzable_request.get_uri(),
                                            cache=False)
        except:
            om.out.debug('Failed to retrieve the page for finding image sources.')
        else:
            try:
                document_parser = parser_cache.dpc.get_document_parser_for(response)
            except BaseFrameworkException:
                return []

            image_path_list = document_parser.get_references_of_tag('img')

            for path in image_path_list:
                res.append(path)

        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Checks if the remote IIS is vulnerable to MS15-034 by sending one HTTP
        request containing the `Range: bytes=0-18446744073709551615` header.

        Warning: In some strange scenarios this test can cause a Denial of
        Service.
        """

