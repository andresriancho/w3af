"""
intercept_handler.py

Copyright 2008 Andres Riancho

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
import time
import traceback

from w3af.core.controllers.daemons.proxy import ProxyHandler


class InterceptProxyHandler(ProxyHandler):
    """
    The handler that traps requests and adds them to the queue.
    """
    def handle_request(self, flow):
        """
        This method handles EVERY request that was send by the browser, we
        decide if the request needs to be trapped and queue it if needed.

        :param flow: A libmproxy flow containing the request
        """
        http_request = self._to_w3af_request(flow.request)

        try:
            # Now we check if we need to add this to the queue, or just let
            # it go through.
            if self._should_be_trapped(http_request):
                http_response = self._do_trap(http_request)
            else:
                # Send the request to the remote webserver
                http_response = self._send_http_request(http_request)
        except Exception, e:
            trace = str(traceback.format_exc())
            http_response = self._create_error_response(http_request, None, e,
                                                        trace=trace)

        # Send the response (success|error) to the browser
        http_response = self._to_libmproxy_response(flow.request, http_response)
        flow.reply(http_response)

    def send_raw_request(self, orig_fuzzable_req, head, postdata):
        # the handler is polling this dict and will extract the information
        # from it and then send it to the remote web server
        self.edited_requests[id(orig_fuzzable_req)] = (head, postdata)

        # Loop until I get the data from the remote web server
        for i in xrange(60):
            time.sleep(0.1)
            if id(orig_fuzzable_req) in self.edited_responses:
                res = self.edited_responses[id(orig_fuzzable_req)]
                del self.edited_responses[id(orig_fuzzable_req)]

                # Now we return it...
                if isinstance(res, tuple) and isinstance(res[0], Exception):
                    exception, value, _traceback = res
                    raise exception, value, _traceback
                else:
                    return res

        # I looped and got nothing!
        msg = 'Timed out waiting for response from remote server.'
        raise BaseFrameworkException(msg)

    def _do_trap(self, http_request):
        """
        Wait for the user to modify the request
        :param http_request: A w3af HTTP request instance
        :return: An HTTP response
        """
        # Add it to the request queue, and wait for the user to edit the
        # request...
        self.server.request_queue.put(http_request)
        edited_requests = self.server.edited_requests

        while True:

            if not id(http_request) in edited_requests:
                time.sleep(0.1)
                continue

            head, body = edited_requests[id(http_request)]
            del edited_requests[id(http_request)]

            if head is None and body is None:
                # The request was dropped by the user. Send 403 and break
                # TODO: send_error!
                return self.send_error(http_request,
                                       'The HTTP request was dropped by the user', 403)
            else:
                # The request was edited by the user
                # Send it to the remote web server and to the proxy user
                # interface.
                try:
                    # TODO: name?
                    http_request = HTTPRequest.from_raw(head, body)
                    res = self._send_http_request(http_request)
                except Exception, e:
                    # TODO: who handles this?
                    res = e

                # Save it so the upper layer can read this response.
                self.server.edited_responses[id(http_request)] = res

                # From here, we send it to the browser
                return res

    def _should_be_trapped(self, fuzzable_request):
        """
        Determine, based on the user configured parameters:
            - self.what_to_trap
            - self.methods_to_trap
            - self.what_not_to_trap
            - self.trap
        If the request needs to be trapped or not.

        :param fuzzable_request: The request to analyze.
        """
        if not self.server.trap:
            return False

        if (len(self.server.methods_to_trap) and
        fuzzable_request.get_method() not in self.server.methods_to_trap):
            return False

        url_string = fuzzable_request.get_url().url_string
        if self.server.what_not_to_trap.search(url_string):
            return False

        if not self.server.what_to_trap.search(url_string):
            return False

        return True
