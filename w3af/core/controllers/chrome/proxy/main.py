"""
main.py

Copyright 2019 Andres Riancho

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
import threading

from w3af.core.controllers.daemons.proxy import Proxy
from w3af.core.controllers.chrome.proxy.handler import LoggingHandler


class LoggingProxy(Proxy):
    def __init__(self, ip, port, uri_opener, handler_klass=LoggingHandler,
                 ca_certs=Proxy.CA_CERT_DIR, name='LoggingProxyThread',
                 queue=None):
        """
        Override the parent init so we can save the plugin reference, all the
        rest is just the same.
        """
        super(LoggingProxy, self).__init__(ip, port, uri_opener,
                                           handler_klass=handler_klass,
                                           ca_certs=ca_certs,
                                           name=name)
        self.queue = queue
        self.debugging_id = None

        self.first_http_response = None
        self.first_http_request = None
        self.first_lock = threading.RLock()

        self._http_request_count_lock = threading.RLock()
        self._pending_http_request_count = 0

    def set_first_request_response(self, fuzzable_request, http_response):
        with self.first_lock:
            if self.first_http_response is not None:
                return

            # I don't want to save redirects, that would mess-up the parsing
            # with DocumentParser because the base URL would be incorrect
            if http_response.get_code() in range(300, 400):
                return

            self.first_http_response = http_response
            self.first_http_request = fuzzable_request

    def get_first_response(self):
        return self.first_http_response

    def get_first_request(self):
        return self.first_http_request

    def set_debugging_id(self, debugging_id):
        self.debugging_id = debugging_id
        self.first_http_request = None
        self.first_http_response = None

    def set_traffic_queue(self, http_traffic_queue):
        self.queue = http_traffic_queue
        self.first_http_request = None
        self.first_http_response = None

    def stop(self):
        super(LoggingProxy, self).stop()
        self.set_traffic_queue(None)
        self.set_debugging_id(None)
        self.first_http_request = None
        self.first_http_response = None

    def increase_pending_http_request_count(self):
        with self._http_request_count_lock:
            self._pending_http_request_count += 1

    def decrease_pending_http_request_count(self):
        with self._http_request_count_lock:
            self._pending_http_request_count -= 1

    def get_pending_http_request_count(self):
        return self._pending_http_request_count
