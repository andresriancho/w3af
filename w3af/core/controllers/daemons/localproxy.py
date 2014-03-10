"""
localproxy.py

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
import os
import Queue
import re
import time
import traceback

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.daemons.proxy import Proxy, w3afProxyHandler
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.parsers.HTTPRequestParser import HTTPRequestParser
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class w3afLocalProxyHandler(w3afProxyHandler):
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
            # Now we check if we need to add this to the queue, or just let
            # it go through.
            if self._should_be_trapped(fuzzable_request):
                res = self._do_trap(fuzzable_request)
            else:
                # Send the request to the remote webserver
                res = self._send_fuzzable_request(fuzzable_request)
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
        self.server.w3afLayer._request_queue.put(fuzzable_request)
        edited_requests = self.server.w3afLayer._edited_requests
        
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
                # Send it to the remote web server and to the proxy user interface.

                if self.server.w3afLayer._fix_content_length:
                    head, body = self._fix_content_length(head, body)

                try:
                    res = self._uri_opener.send_raw_request(head, body)
                except Exception, e:
                    res = e

                # Save it so the upper layer can read this response.
                self.server.w3afLayer._edited_responses[
                    id(fuzzable_request)] = res

                # From here, we send it to the browser
                return res
                

    def _fix_content_length(self, head, postdata):
        """
        The user may have changed the postdata of the request, and not the
        content-length header; so we are going to fix that problem.
        """
        fuzzable_request = HTTPRequestParser(head, postdata)
        
        if fuzzable_request.get_data() is None:
            # Nothing to do here
            return head, postdata
        
        headers = fuzzable_request.get_headers()
        headers['content-length'] = [str(len(fuzzable_request.get_data())), ]

        fuzzable_request.set_headers(headers)
        head = fuzzable_request.dump_request_head()
        return head, postdata

    def _send_fuzzable_request(self, fuzzable_request):
        """
        Sends a fuzzable request to the remote web server.
        """
        uri = fuzzable_request.get_uri()
        data = fuzzable_request.get_data()
        headers = fuzzable_request.get_headers()
        method = fuzzable_request.get_method()
        
        # Also add the cookie header.
        cookie = fuzzable_request.get_cookie()
        if cookie:
            headers['Cookie'] = str(cookie)

        args = (uri, )
        functor = getattr(self._uri_opener, method)
        # run functor , run !   ( forest gump flash )
        res = apply(functor, args, {'data': data, 'headers':
                    headers, 'grep': True})
        return res

    def _should_be_trapped(self, fuzzable_request):
        """
        Determine, based on the user configured parameters:
            - self._what_to_trap
            - self._methods_to_trap
            - self._what_not_to_trap
            - self._trap

        If the request needs to be trapped or not.
        :param fuzzable_request: The request to analyze.
        """
        if not self.server.w3afLayer._trap:
            return False

        if len(self.server.w3afLayer._methods_to_trap) and \
                fuzzable_request.get_method() not in self.server.w3afLayer._methods_to_trap:
            return False

        if self.server.w3afLayer._what_not_to_trap.search(fuzzable_request.get_url().url_string):
            return False

        if not self.server.w3afLayer._what_to_trap.search(fuzzable_request.get_url().url_string):
            return False

        return True


class LocalProxy(Proxy):
    """
    This is the local proxy server that is used by the local proxy GTK user
    interface to perform all its magic ;)
    """

    def __init__(self, ip, port, urlOpener=ExtendedUrllib(),
                 proxy_cert=Proxy.SSL_CERT):
        """
        :param ip: IP address to bind
        :param port: Port to bind
        :param urlOpener: The urlOpener that will be used to open the requests
                          that arrive from the browser
        :param proxyHandler: A class that will know how to handle requests
                             from the browser
        :param proxy_cert: Proxy certificate to use, this is needed for
                           proxying SSL connections.
        """
        Proxy.__init__(self, ip, port, urlOpener, w3afLocalProxyHandler,
                       proxy_cert)

        self.daemon = True
        self.name = 'LocalProxyThread'

        # Internal vars
        self._request_queue = Queue.Queue()
        self._edited_requests = {}
        self._edited_responses = {}

        # User configured parameters
        self._methods_to_trap = set()
        self._what_to_trap = re.compile('.*')
        self._what_not_to_trap = re.compile('.*\.(gif|jpg|png|css|js|ico|swf|axd|tif)$')
        self._trap = False
        self._fix_content_length = True

    def get_trapped_request(self):
        """
        To be called by the gtk user interface every 400ms.
        :return: A fuzzable request object, or None if the queue is empty.
        """
        try:
            return self._request_queue.get(block=False)
        except Queue.Empty:
            return None

    def set_what_to_trap(self, regex):
        """Set regular expression that indicates what URLs NOT TO trap."""
        try:
            self._what_to_trap = re.compile(regex)
        except re.error:
            error = 'The regular expression you configured is invalid.'
            raise BaseFrameworkException(error)

    def set_methods_to_trap(self, methods):
        """Set list that indicates what METHODS TO trap.

           If list is empty then we will trap all methods
        """
        self._methods_to_trap = set(i.upper() for i in methods)

    def set_what_not_to_trap(self, regex):
        """Set regular expression that indicates what URLs TO trap."""
        try:
            self._what_not_to_trap = re.compile(regex)
        except re.error:
            error = 'The regular expression you configured is invalid.'
            raise BaseFrameworkException(error)

    def set_trap(self, trap):
        """
        :param trap: True if we want to trap requests.
        """
        self._trap = trap

    def get_trap(self):
        return self._trap

    def set_fix_content_length(self, fix):
        """Set Fix Content Length flag."""
        self._fix_content_length = fix

    def get_fix_content_length(self):
        """Get Fix Content Length flag."""
        return self._fix_content_length

    def drop_request(self, orig_fuzzable_req):
        """Let the handler know that the request was dropped."""
        self._edited_requests[id(orig_fuzzable_req)] = (None, None)

    def send_raw_request(self, orig_fuzzable_req, head, postdata):
        # the handler is polling this dict and will extract the information
        # from it and then send it to the remote web server
        self._edited_requests[id(orig_fuzzable_req)] = (head, postdata)

        # Loop until I get the data from the remote web server
        for i in xrange(60):
            time.sleep(0.1)
            if id(orig_fuzzable_req) in self._edited_responses:
                res = self._edited_responses[id(orig_fuzzable_req)]
                del self._edited_responses[id(orig_fuzzable_req)]
                # Now we return it...
                if isinstance(res, Exception):
                    raise res
                else:
                    return res

        # I looped and got nothing!
        raise BaseFrameworkException(
            'Timed out waiting for response from remote server.')

