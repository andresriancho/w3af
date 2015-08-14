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
import Queue

from w3af.core.controllers.daemons.proxy import Proxy
from w3af.core.controllers.daemons.proxy import InterceptProxyHandler
from w3af.core.controllers.exceptions import ProxyException


class InterceptProxy(Proxy):
    """
    This is the local proxy server that is used by the local proxy GTK user
    interface to perform all its magic ;)
    """

    DEFAULT_NO_TRAP = '.*\.(gif|jpg|png|css|js|ico|swf|axd|tif)$'
    DEFAULT_TRAP = '.*'

    def __init__(self, ip, port, url_opener):
        """
        :param ip: IP address to bind
        :param port: Port to bind
        :param url_opener: The urlOpener that will be used to open the requests
                          that arrive from the browser
        """
        Proxy.__init__(self, ip, port, url_opener,
                       handler_klass=InterceptProxyHandler,
                       name='LocalProxyThread')

        # Internal vars
        self.requests_pending_modification = Queue.Queue()
        self.requests_already_modified = Queue.Queue()

        # User configured parameters
        self.methods_to_trap = set()
        self.what_to_trap = re.compile(self.DEFAULT_TRAP)
        self.what_not_to_trap = re.compile(self.DEFAULT_NO_TRAP)
        self.trap = False

        # Forward to handler
        # pylint: disable=E1103
        self.on_request_edit_finished = self._master.on_request_edit_finished

    def get_trapped_request(self):
        """
        To be called by the gtk user interface every 400ms.
        :return: A fuzzable request object, or None if the queue is empty.
        """
        try:
            return self.requests_pending_modification.get(block=False)
        except Queue.Empty:
            return None

    def set_what_to_trap(self, regex):
        """
        Set regular expression that indicates what URLs NOT TO trap.
        """
        try:
            self.what_to_trap = re.compile(regex)
        except re.error:
            error = 'The regular expression you configured is invalid.'
            raise ProxyException(error)

    def set_methods_to_trap(self, methods):
        """
        Set list that indicates what METHODS TO trap.
        If list is empty then we will trap all methods
        """
        self.methods_to_trap = set(i.upper() for i in methods)

    def set_what_not_to_trap(self, regex):
        """
        Set regular expression that indicates what URLs TO trap.
        """
        try:
            self.what_not_to_trap = re.compile(regex)
        except re.error:
            error = 'The regular expression you configured is invalid.'
            raise ProxyException(error)

    def set_trap(self, trap):
        """
        :param trap: True if we want to trap requests.
        """
        self.trap = trap

    def get_trap(self):
        return self.trap

    def drop_request(self, http_request):
        """
        Let the handler know that the request was dropped.
        """
        # pylint: disable=E1103
        return self._master.on_request_drop(http_request)
