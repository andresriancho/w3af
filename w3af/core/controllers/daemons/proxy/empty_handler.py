"""
empty_handler.py

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

from mitmproxy.controller import handler


class EmptyHandler(object):

    @handler
    def log(self, l):
        pass

    @handler
    def clientconnect(self, root_layer):
        pass

    @handler
    def clientdisconnect(self, root_layer):
        pass

    @handler
    def serverconnect(self, server_conn):
        pass

    @handler
    def serverdisconnect(self, server_conn):
        pass

    @handler
    def next_layer(self, top_layer):
        pass

    @handler
    def http_connect(self, flow):
        pass

    @handler
    def error(self, flow):
        pass

    @handler
    def requestheaders(self, flow):
        pass

    @handler
    def request(self, flow):
        pass

    @handler
    def responseheaders(self, flow):
        pass

    @handler
    def response(self, flow):
        pass

    @handler
    def websocket_handshake(self, flow):
        pass

    @handler
    def websocket_start(self, flow):
        pass

    @handler
    def websocket_message(self, flow):
        pass

    @handler
    def websocket_error(self, flow):
        pass

    @handler
    def websocket_end(self, flow):
        pass

    @handler
    def tcp_start(self, flow):
        pass

    @handler
    def tcp_message(self, flow):
        pass

    @handler
    def tcp_error(self, flow):
        pass

    @handler
    def tcp_end(self, flow):
        pass
