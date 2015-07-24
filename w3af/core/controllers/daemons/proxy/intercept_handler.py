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
import traceback

from w3af.core.controllers.daemons.proxy import ProxyHandler
from w3af.core.data.parsers.doc.http_request_parser import http_request_parser
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.controllers.daemons.proxy.templates.utils import render


class InterceptProxyHandler(ProxyHandler):
    """
    The handler that traps requests and adds them to the queue.
    """
    def handle_request_in_thread(self, flow):
        """
        The handle_request method is run in the same thread each time, so we
        need to run in a thread.

        :param flow: A libmproxy flow containing the request
        :return: None, we reply to flow
        """
        http_request = self._to_w3af_request(flow.request)

        try:
            # Now we check if we need to add this to the queue, or just let
            # it go through.
            if self._should_be_trapped(http_request):
                http_response = self.on_start_edit_request(http_request)
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

    def on_request_drop(self, http_request):
        """
        When the UI calls "drop request" we need to modify our queues

        :param http_request: The request to drop
        :return: None, simply queue a "Request drop HTTP response"
        """
        content = render('drop.html', {})

        headers = Headers((
            ('Connection', 'close'),
            ('Content-type', 'text/html'),
        ))

        http_response = HTTPResponse(403,
                                     content.encode('utf-8'),
                                     headers,
                                     http_request.get_uri(),
                                     http_request.get_uri(),
                                     msg='Request drop')

        self.parent_process.requests_already_modified.put(http_response)

    def on_request_edit_finished(self, orig_http_request, head, post_data):
        """
        This method is called when the user finishes editing the request that
        will be sent to the wire.

        :param orig_http_request: The original HTTP request
        :param head: The headers for the modified request
        :param post_data: The post-data for the modified request
        :return: The HTTP response
        """
        try:
            http_request = http_request_parser(head, post_data)
            http_response = self._send_http_request(http_request)
        except Exception, e:
            trace = str(traceback.format_exc())
            http_response = self._create_error_response(orig_http_request,
                                                        None, e, trace=trace)

        self.parent_process.requests_already_modified.put(http_response)
        return http_response

    def on_start_edit_request(self, http_request):
        """
        Wait for the user to modify the request. After editing the request the
        code should call on_edited_request.

        :param http_request: A w3af HTTP request instance
        :return: An HTTP response
        """
        self.parent_process.requests_pending_modification.put(http_request)
        return self.parent_process.requests_already_modified.get()

    def _should_be_trapped(self, http_request):
        """
        Determine, based on the user configured parameters:
            - self.what_to_trap
            - self.methods_to_trap
            - self.what_not_to_trap
            - self.trap
        If the request needs to be trapped or not.

        :param http_request: The request to analyze.
        """
        if not self.parent_process.trap:
            return False

        if (len(self.parent_process.methods_to_trap) and
        http_request.get_method() not in self.parent_process.methods_to_trap):
            return False

        url_string = http_request.get_uri().uri2url().url_string
        if self.parent_process.what_not_to_trap.search(url_string):
            return False

        if not self.parent_process.what_to_trap.search(url_string):
            return False

        return True
