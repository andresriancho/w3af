"""
xst.py

Copyright 2007 Andres Riancho

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

import w3af.core.controllers.output_manager as om

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers
from w3af.core.data.kb.vuln import Vuln


class xst(AuditPlugin):
    """
    Find Cross Site Tracing vulnerabilities.

    :author: Josh Summitt (ascetik@gmail.com)
    :author: Andres Riancho (andres@gmail.com) - Rewrite 27 Jul 2012
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._exec = True

    def audit(self, freq, orig_response, debugging_id):
        """
        Verify xst vulns by sending a TRACE request and analyzing the response.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        if not self._exec:
            return

        # Only run once
        self._exec = False

        uri = freq.get_url().get_domain_path()
        method = 'TRACE'
        headers = Headers()
        headers['FakeHeader'] = 'XST'
        fr = FuzzableRequest(uri,
                             method=method,
                             headers=headers
                             )

        # send the request to the server and receive the response
        response = self._uri_opener.send_mutant(fr)

        # create a regex to test the response.
        regex = re.compile("FakeHeader: *?XST", re.IGNORECASE)
        if regex.search(response.get_body()):
            # If vulnerable record it. This will now become visible on
            # the KB Browser
            desc = 'The web server at "%s" is vulnerable to Cross Site'\
                  ' Tracing.'
            desc = desc % response.get_url()

            v = Vuln.from_fr('Cross site tracing vulnerability', desc,
                             severity.LOW, response.id, self.get_name(),
                             freq)

            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            self.kb_append(self, 'xst', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds the Cross Site Tracing (XST) vulnerability.
        
        The TRACE method echos back requests sent to it. This plugin sends a
        TRACE request to the server and if the request is echoed back then XST
        is confirmed.

        No configurable parameters are available.
        """
