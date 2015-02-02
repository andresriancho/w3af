"""
ssl_daemon.py

Copyright 2015 Andres Riancho

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
import SocketServer
import ssl
import os

from .upper_daemon import UpperDaemon


class RawSSLDaemon(UpperDaemon):
    """
    Echo the data sent by the client, but upper case it first. SSL version of
    UpperDaemon.
    """
    def run(self):
        self.server = SocketServer.TCPServer(self.server_address, self.handler,
                                             bind_and_activate=False)

        key_file = os.path.join(os.path.dirname(__file__), 'unittest.key')
        cert_file = os.path.join(os.path.dirname(__file__), 'unittest.crt')

        self.server.socket = ssl.wrap_socket(self.server.socket,
                                             keyfile=key_file,
                                             certfile=cert_file,
                                             cert_reqs=ssl.CERT_NONE,
                                             ssl_version=ssl.PROTOCOL_TLSv1)

        self.server.server_bind()
        self.server.server_activate()
        self.server.serve_forever()


