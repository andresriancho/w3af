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
import re
import sys
import time
import Queue
import traceback

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.daemons.proxy import Proxy, ProxyHandler
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.parsers.doc.http_request_parser import http_request_parser
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class InterceptProxyHandler(ProxyHandler):
    """
    The handler that traps requests and adds them to the queue.
    """
    def do_ALL(self):
        """
        This method handles EVERY request that were send by the browser.
        """
        # First of all, we create a fuzzable request based on the attributes
        # that are set to this object
        fuzzable_request = self._create_fuzzable_request()

        try:
            should_trap = self._should_be_trapped(fuzzable_request)
        except Exception, e:
            self._send_error(e, trace=str(traceback.format_exc()))
            return

        try:
            # Now we check if we need to add this to the queue, or just let
            # it go through.
            if should_trap:
                res = self._do_trap(fuzzable_request)
            else:
                # Send the request to the remote webserver
                res = self._uri_opener.send_mutant(fuzzable_request, grep=True)
        except Exception, e:
            self._send_error(e, trace=str(traceback.format_exc()))
        else:
            try:
                self._send_to_browser(res)
            except Exception, e:
                error = 'Exception found while sending response to the'\
                        ' browser. Exception description: "%s".'
                om.out.debug(error % e)

    def _do_trap(self, fuzzable_request):
        # Add it to the request queue, and wait for the user to edit the
        # request...
        self.server.w3afLayer.request_queue.put(fuzzable_request)
        edited_requests = self.server.w3afLayer.edited_requests
        
        while True:
            
            if not id(fuzzable_request) in edited_requests:
                time.sleep(0.1)
                continue
            
            head, body = edited_requests[id(fuzzable_request)]
            del edited_requests[id(fuzzable_request)]

            if head == body is None:
                # The request was dropped by the user. Send 403 and break
                self.send_response(403)
                
                self.send_header('Connection', 'close')
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write('The HTTP request was dropped by the user')
                
                self.rfile.close()
                self.wfile.close()
                break

            else:
                # The request was edited by the user
                #
                # Send it to the remote web server and to the proxy user
                # interface.

                if self.server.w3afLayer.fix_content_length:
                    head, body = self.do_fix_content_length(head, body)

                try:
                    res = self._uri_opener.send_raw_request(head, body)
                except Exception:
                    res = sys.exc_info()

                # Save it so the upper layer can read this response.
                fr_id = id(fuzzable_request)
                self.server.w3afLayer.edited_responses[fr_id] = res

                # From here, we send it to the browser
                return res
                
    def do_fix_content_length(self, head, postdata):
        """
        The user may have changed the postdata of the request, and not the
        content-length header; so we are going to fix that problem.
        """
        fuzzable_request = http_request_parser(head, postdata)
        headers = fuzzable_request.get_headers()

        if not fuzzable_request.get_data():
            # In the past, maybe, we had a post-data. Now we don't have any,
            # so we'll remove the content-length
            try:
                headers.idel('content-length')
            except KeyError:
                pass

        else:
            # We now have a post-data, so we better set the content-length
            headers['content-length'] = str(len(fuzzable_request.get_data()))

        head = fuzzable_request.dump_request_head()

        return head, postdata

    def _should_be_trapped(self, freq):
        """
        Determine, based on the user configured parameters:
            - self.what_to_trap
            - self._methods_to_trap
            - self._what_not_to_trap
            - self._trap

        If the request needs to be trapped or not.
        :param freq: The request to analyze.
        """
        conf = self.server.w3afLayer

        if not conf._trap:
            return False

        methods_to_trap = conf.methods_to_trap

        if len(methods_to_trap) and freq.get_method() not in methods_to_trap:
            return False

        if conf.what_not_to_trap.search(freq.get_url().url_string):
            return False

        if not conf.what_to_trap.search(freq.get_url().url_string):
            return False

        return True
