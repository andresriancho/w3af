"""
intercept_proxy.py

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


class InterceptProxy(Proxy):
    """
    This is the local proxy server that is used by the local proxy GTK user
    interface to perform all its magic ;)
    """

    def __init__(self, ip, port, url_opener=ExtendedUrllib()):
        """
        :param ip: IP address to bind
        :param port: Port to bind
        :param url_opener: The urlOpener that will be used to open the requests
                          that arrive from the browser
        """
        Proxy.__init__(self, ip, port, url_opener, LocalProxyHandler,
                       name='LocalProxyThread')

        # Internal vars
        self.request_queue = Queue.Queue()
        self.edited_requests = {}
        self.edited_responses = {}

        # User configured parameters
        self.methods_to_trap = set()
        self.what_to_trap = re.compile('.*')
        self.what_not_to_trap = re.compile('.*\.(gif|jpg|png|css|js|ico|swf|axd|tif)$')
        self._trap = False
        self.fix_content_length = True

    def get_trapped_request(self):
        """
        To be called by the gtk user interface every 400ms.
        :return: A fuzzable request object, or None if the queue is empty.
        """
        try:
            return self.request_queue.get(block=False)
        except Queue.Empty:
            return None

    def set_what_to_trap(self, regex):
        """Set regular expression that indicates what URLs NOT TO trap."""
        try:
            self.what_to_trap = re.compile(regex)
        except re.error:
            error = 'The regular expression you configured is invalid.'
            raise BaseFrameworkException(error)

    def set_methods_to_trap(self, methods):
        """Set list that indicates what METHODS TO trap.

           If list is empty then we will trap all methods
        """
        self.methods_to_trap = set(i.upper() for i in methods)

    def set_what_not_to_trap(self, regex):
        """Set regular expression that indicates what URLs TO trap."""
        try:
            self.what_not_to_trap = re.compile(regex)
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
        self.fix_content_length = fix

    def get_fix_content_length(self):
        """Get Fix Content Length flag."""
        return self.fix_content_length

    def drop_request(self, orig_fuzzable_req):
        """Let the handler know that the request was dropped."""
        self.edited_requests[id(orig_fuzzable_req)] = (None, None)

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
