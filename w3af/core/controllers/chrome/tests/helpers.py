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
import os
import tempfile
import BaseHTTPServer

from urlparse import urlparse

import w3af.core.controllers.output_manager as om

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.controllers.w3afCore import w3afCore


def set_debugging_in_output_manager():
    w3af_core = w3afCore()
    text_file_inst = w3af_core.plugins.get_plugin_inst('output', 'text_file')

    output_dir = tempfile.gettempdir()
    rnd = rand_alnum(6)

    text_output = os.path.join(output_dir, 'output-%s.txt' % rnd)
    http_output = os.path.join(output_dir, 'output-http-%s.txt' % rnd)

    default_opts = text_file_inst.get_options()
    default_opts['output_file'].set_value(text_output)
    default_opts['http_output_file'].set_value(http_output)
    default_opts['verbose'].set_value(True)
    text_file_inst.set_options(default_opts)

    om.manager.set_output_plugin_inst(text_file_inst)
    om.manager.start()

    print('')
    print('    Logging to %s' % text_output)

    latest_output = os.path.join(tempfile.gettempdir(), 'latest-w3af-output.txt')
    if os.path.exists(latest_output):
        os.remove(latest_output)

    os.symlink(text_output, latest_output)
    print('    Symlink to log file created at %s' % latest_output)


def debugging_is_configured_in_output_manager():
    return bool(om.manager.get_output_plugin_inst())


class ExtendedHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    RESPONSE_BODY = u'<html><head></head><body>Hello world</body></html>'

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

        headers = {
            'Content-Type': 'text/html',
            'Content-Length': len(body),
            'Content-Encoding': 'identity'
        }

        self.send_response_to_client(code, body, headers)

    def send_response_to_client(self, code, body, headers):
        try:
            self.send_response(code)

            for name, value in headers.iteritems():
                self.send_header(name, value)

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
