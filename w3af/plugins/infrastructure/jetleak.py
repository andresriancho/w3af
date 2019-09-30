"""
jetleak.py

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
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.constants.severity import HIGH
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.vuln import Vuln


class jetleak(InfrastructurePlugin):
    """
    Detect CVE-2015-2080 aka. JetLeak
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Detect CVE-2015-2080 aka. JetLeak

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        url = fuzzable_request.get_url()
        headers = Headers([('Referer', '\x00')])

        response = self._uri_opener.GET(url,
                                        cache=False,
                                        grep=False,
                                        headers=headers)

        if response.get_code() != 400:
            return

        if 'Illegal character 0x0 in state' not in response.get_msg():
            return

        desc = ('The application appears to be running a version of Jetty'
                ' vulnerable to CVE-2015-2080, which allows attackers to'
                ' read arbitrary server memory buffers')

        v = Vuln('JetLeak', desc, HIGH, response.id, self.get_name())
        v.set_url(response.get_url())

        self.kb_append_uniq(self, 'jetleak', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Detect CVE-2015-2080 Jetty vulnerability also known as JetLeak
        """

