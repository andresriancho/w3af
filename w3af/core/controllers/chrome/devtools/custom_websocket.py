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
import six
import time
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

        self.frame_buffer = CustomFrameBuffer(self._recv,
                                              self,
                                              skip_utf8_validation)

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
    def __init__(self, recv_fn, websocket, skip_utf8_validation):
        super(CustomFrameBuffer, self).__init__(recv_fn, skip_utf8_validation)
        self._websocket = websocket

    def recv_strict(self, bufsize):
        """
        Overriding to fix the issue with timeout handling which is explained
        in [0].

        [0] https://github.com/websocket-client/websocket-client/issues/437

        :param bufsize: The size of the buffer to read
        :return: The bytes read from the wire
        """
        timeout_secs = self._websocket.gettimeout()
        timeout_timestamp = time.time() + timeout_secs

        shortage = bufsize - sum(len(x) for x in self.recv_buffer)
        while shortage > 0 and time.time() < timeout_timestamp:
            # Limit buffer size that we pass to socket.recv() to avoid
            # fragmenting the heap -- the number of bytes recv() actually
            # reads is limited by socket buffer and is relatively small,
            # yet passing large numbers repeatedly causes lots of large
            # buffers allocated and then shrunk, which results in
            # fragmentation.
            #
            # This is an undercover call to CustomWebSocket._recv() which then
            # calls custom_recv() defined below
            bytes_ = self.recv(min(16384, shortage))
            self.recv_buffer.append(bytes_)
            shortage -= len(bytes_)

        unified = six.b('').join(self.recv_buffer)

        if shortage == 0:
            self.recv_buffer = []
            return unified
        else:
            self.recv_buffer = [unified[bufsize:]]
            return unified[:bufsize]


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
