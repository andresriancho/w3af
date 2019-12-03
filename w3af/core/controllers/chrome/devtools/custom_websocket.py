"""
custom_websocket.py

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
import socket

from websocket import (WebSocket,
                       WebSocketConnectionClosedException,
                       WebSocketTimeoutException,
                       frame_buffer)


class CustomWebSocket(WebSocket):
    def __init__(self,
                 sslopt=None,
                 sockopt=None,
                 fire_cont_frame=False,
                 enable_multithread=False,
                 skip_utf8_validation=False):
        super(CustomWebSocket, self).__init__(sslopt=sslopt,
                                              sockopt=sockopt,
                                              get_mask_key=get_mask_key_zero,
                                              fire_cont_frame=fire_cont_frame,
                                              enable_multithread=enable_multithread,
                                              #
                                              # UTF-8 validation in the websocket library
                                              # is a very CPU-intensive process which, in
                                              # some cases can take a LONG time
                                              #
                                              # Disabling this in order to prevent timeouts
                                              # when reading from the websocket
                                              #
                                              skip_utf8_validation=True)

        self.frame_buffer = CustomFrameBuffer(self._recv, skip_utf8_validation)

    def set_mask_key(self, *args):
        # Do not let anyone override this
        self.get_mask_key = get_mask_key_zero

    def _recv(self, bufsize):
        try:
            return custom_recv(self.sock, bufsize)
        except (WebSocketConnectionClosedException, WebSocketTimeoutException):
            if self.sock:
                self.sock.close()
            self.sock = None
            self.connected = False
            raise


class CustomFrameBuffer(frame_buffer):
    def recv_strict(self, bufsize):
        """
        Overriding to fix the issue with timeout handling which is explained
        in [0].

        [0] https://github.com/websocket-client/websocket-client/issues/437

        :param bufsize: The size of the buffer to read
        :return: The bytes read from the wire
        """
        # This is an undercover call to CustomWebSocket._recv() which then
        # calls custom_recv() defined below
        return self.recv(bufsize)


def get_mask_key_zero(key_length):
    return '\x00' * key_length


def custom_recv(sock, bufsize):
    if not sock:
        raise WebSocketConnectionClosedException('Socket is already closed')

    if sock.gettimeout() == 0:
        data = sock.recv(bufsize)
    else:
        data = recv_with_timeout(sock, bufsize)

    if not data:
        raise WebSocketConnectionClosedException('Connection is already closed')

    if len(data) != bufsize:
        raise WebSocketConnectionClosedException('Connection was closed by peer')

    return data


def recv_with_timeout(sock, bufsize):
    """
    Read `bufsize` bytes from socket `sock` using a timeout.

    :param sock: The socket from which data is read
    :param bufsize: The number of bytes to read
    :return: Bytes that came from the socket
    """
    try:
        return sock.recv(bufsize)
    except socket.timeout:
        return ''
