"""
helpers.py

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
import BaseHTTPServer

from urlparse import urlparse


class ExtendedHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    RESPONSE_BODY = '<body>Hello world</body>'

    def get_code_body(self, request_path):
        """
        This is the method you want to override in your handlers!

        :param request_path: The HTTP request path (does not include domain nor protocol)
        :return: The HTTP response code and body to send as result
        """
        return 200, self.RESPONSE_BODY

    def do_GET(self):
        """
        Handles HTTP GET requests to the server.

        Extract the path and send it to get_code_body() which is usually the
        method you want to override.

        :return: None
        """
        request_path = urlparse(self.path).path
        code, body = self.get_code_body(request_path)
        self.send_response_to_client(code, body)

    def send_response_to_client(self, code, body):
        try:
            self.send_response(code)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(body))
            self.send_header('Content-Encoding', 'identity')
            self.end_headers()
            self.wfile.write(body)
        except Exception, e:
            print('Exception: "%s".' % e)
        finally:
            # Clean up
            self.close_connection = 1
            self.rfile.close()
            self.wfile.close()
            return

    def log_message(self, fmt, *args):
        """
        I don't want messages to be written to stderr, please ignore them. If
        we don't override this method I end up with messages like:

            eulogia.local - - [19/Oct/2012 10:12:33] "GET /GGC8s1dk HTTP/1.0" 200 -

        Being printed to the console while running unittests.
        """
        pass
