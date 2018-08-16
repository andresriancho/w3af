"""
un_ssl.py

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

import w3af.core.data.constants.severity as severity

from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.exceptions import (ScanMustStopException,
                                              HTTPRequestException)


class un_ssl(AuditPlugin):
    """
    Find out if secure content can also be fetched using http.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._should_run = True

    def audit(self, freq, orig_response, debugging_id):
        """
        Check if the protocol specified in freq is https and fetch the same URL
        using http. ie:
            - input: https://w3af.org/
            - check: http://w3af.org/

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        if not self._should_run:
            return

        initial_uri = freq.get_uri()
        if initial_uri.get_port() not in {80, 443}:
            # We get here then the original URL looks like http://foo:3921/
            #
            # It's really strange (maybe not even possible?) to find a server
            # that listens for HTTP and HTTPS connections on the same port,
            # since we don't want to guess the port, nor generate errors such
            # as #8871 we just ignore this case
            self._should_run = False
            return

        # Define some variables
        insecure_uri = initial_uri.copy()
        secure_uri = initial_uri.copy()

        insecure_uri.set_protocol('http')
        insecure_fr = copy.deepcopy(freq)
        insecure_fr.set_url(insecure_uri)

        secure_uri.set_protocol('https')
        secure_fr = copy.deepcopy(freq)
        secure_fr.set_url(secure_uri)

        # Make sure that we disable error handling during these tests, we want
        # the requests to fail quickly and without affecting the library's error
        # rate
        send_mutant = self._uri_opener.send_mutant
        kwargs = {'grep': False, 'error_handling': False}

        try:
            insecure_response = send_mutant(insecure_fr, **kwargs)
            secure_response = send_mutant(secure_fr,  **kwargs)
        except (HTTPRequestException, ScanMustStopException):
            # No vulnerability to report since one of these threw an error
            # (because there is nothing listening on that port). It makes
            # no sense to keep running since we already got an error
            self._should_run = False

        else:
            if insecure_response is None or secure_response is None:
                # No vulnerability to report since one of these threw an
                # error (because there is nothing listening on that port).
                # It makes no sense to keep running since we already got an
                # error
                self._should_run = False
                return

            if self._redirects_to_secure(insecure_response, secure_response):
                return

            if insecure_response.get_code() == secure_response.get_code()\
            and fuzzy_equal(insecure_response.get_body(),
                            secure_response.get_body(),
                            0.95):

                desc = ('Secure content can be accessed using the insecure'
                        ' HTTP protocol. The vulnerable URLs used to verify'
                        ' this vulnerability are:\n'
                        ' - %s\n'
                        ' - %s\n')
                desc %= (secure_uri, insecure_uri)

                response_ids = [insecure_response.id, secure_response.id]

                v = Vuln.from_fr('Secure content over insecure channel',
                                 desc, severity.MEDIUM, response_ids,
                                 self.get_name(), freq)

                self.kb_append(self, 'un_ssl', v)

                # In most cases, when one resource is available, all are
                # so we just stop searching for this vulnerability
                self._should_run = False

    def handle_url_error(self, uri, url_error):
        """
        Override the url error handler because in most cases we'll be connecting
        to a URL which is offline.

        :return: (True: to avoid this exception to be re-raised
                  None: There is no response)
        """
        return False, None

    def _redirects_to_secure(self, insecure_response, secure_response):
        """
        :return: Is the insecure response redirecting to an HTTPS resource?
        """
        if insecure_response.was_redirected():
            redirect_target = insecure_response.get_redir_url()
            
            if redirect_target.get_protocol() == 'https':
                return True
        
        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin verifies that URLs that are available using HTTPS aren't
        available over an insecure HTTP protocol.

        To detect this, the plugin simply requests "https://abc/a.asp" and
        "http://abc.asp" and if both are equal, a vulnerability is found.
        """
