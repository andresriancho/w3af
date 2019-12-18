"""
handler.py

Copyright 2018 Andres Riancho

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.controllers.daemons.proxy import ProxyHandler
from w3af.core.controllers.chrome.proxy.request_modification import add_language_header, remove_user_agent_headless
from w3af.core.controllers.chrome.proxy.response_modification import set_content_encoding, remove_security_headers
from w3af.core.controllers.misc.is_private_site import is_private_site


class LoggingHandler(ProxyHandler):

    def _send_http_request(self,
                           http_request,
                           grep=True,
                           cache=False,
                           debugging_id=None):
        """
        Send a w3af HTTP request to the web server using w3af's HTTP lib,
        capture the HTTP response and send it to the upstream Queue.

        The Queue should be consumed by another part of the code, requests
        and responses should be sent to the framework for further processing.

        No error handling is performed, someone else should do that.

        :param http_request: The request to send
        :return: The response
        """
        domain = http_request.get_uri().get_domain()

        if is_private_site(domain) and not target_is_private_site():
            msg = ('The target site (which is in a public IP address range) is'
                   ' trying to load a resource from a private IP address range.'
                   ' For example, http://public.com/ is trying to load JavaScript,'
                   ' images or CSS from http://127.0.0.1/.\n'
                   '\n'
                   'The scanner is preventing this request to protect itself'
                   ' from SSRF attacks which might be triggered when scanning'
                   ' specially crafted sites.')
            om.out.debug(msg)
            return self._create_error_response(http_request, None, msg)

        remove_user_agent_headless(http_request)
        add_language_header(http_request)

        self.parent_process.increase_pending_http_request_count()

        try:
            http_response = super(LoggingHandler, self)._send_http_request(http_request,
                                                                           grep=grep,
                                                                           cache=True,
                                                                           debugging_id=self.parent_process.debugging_id)
        finally:
            self.parent_process.decrease_pending_http_request_count()

        # Remove security headers to reduce runtime security
        remove_security_headers(http_response)

        # Mangle content-encoding
        set_content_encoding(http_response)

        # Send the request upstream
        fuzzable_request = FuzzableRequest.from_http_request(http_request)
        queue_data = (fuzzable_request,
                      http_response,
                      self.parent_process.debugging_id)

        self.parent_process.queue.put(queue_data)

        self.parent_process.set_first_request_response(fuzzable_request, http_response)

        # Logging for better debugging
        args = (http_request.get_uri(),
                http_response.get_code(),
                len(http_response.get_body()),
                http_response.get_wait_time(),
                http_response.get_from_cache(),
                self.parent_process.debugging_id)
        msg = ('Chrome proxy received HTTP response for %s'
               ' (code: %s, len: %s, rtt: %.2f, from_cache: %s, did: %s)')
        om.out.debug(msg % args)

        return http_response


def target_is_private_site():
    """
    :return: True if the target site w3af is scanning is a private site
             This means that w3af is scanning:

                http://127.0.0.1/
                http://10.1.2.3/

             Or a domain which resolves to a private IP address.

             If the target is not set (this should happen only during
             unittests) the function will return True.
    """
    targets = cf.cf.get('targets')
    if not targets:
        return True

    domain = targets[0].get_domain()
    return is_private_site(domain)
