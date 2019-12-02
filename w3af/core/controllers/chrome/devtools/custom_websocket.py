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
import time
import errno
import socket

from ssl import SSLError
from ssl import SSLWantReadError

from websocket._utils import extract_err_message, extract_error_code
from websocket import (WebSocket,
                       WebSocketConnectionClosedException,
                       WebSocketTimeoutException,
                       frame_buffer)

from w3af.core.controllers.misc.poll import poll


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
                                              skip_utf8_validation=skip_utf8_validation)

        self.frame_buffer = CustomFrameBuffer(self._recv, skip_utf8_validation)

    def set_mask_key(self, *args):
        # Do not let anyone override this
        self.get_mask_key = get_mask_key_zero

    def _recv(self, bufsize):
        try:
            return custom_recv(self.sock, bufsize)
        except WebSocketConnectionClosedException:
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
        # This is an undercover call to custom_recv()
        return self.recv(bufsize)


def get_mask_key_zero(key_length):
    return '\x00' * key_length


def custom_recv(sock, bufsize):
    if not sock:
        raise WebSocketConnectionClosedException('Socket is already closed')

    try:
        if sock.gettimeout() == 0:
            data = sock.recv(bufsize)
        else:
            data = recv_with_timeout(sock, bufsize)
    except socket.timeout as e:
        message = extract_err_message(e)
        raise WebSocketTimeoutException(message)
    except SSLError as e:
        message = extract_err_message(e)
        if isinstance(message, str) and 'timed out' in message:
            raise WebSocketTimeoutException(message)
        else:
            raise

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
    data = ''
    chunk_size = bufsize / 4
    timeout_timestamp = time.time() + sock.gettimeout()

    while True:

        if bufsize == len(data):
            return data

        timeout_reached = time.time() >= timeout_timestamp
        if timeout_reached:
            raise WebSocketTimeoutException('Timeout reading from websocket')

        r, w, e = poll((sock,), (), (), 0.2)

        if not r:
            continue

        try:
            # This call to recv() will timeout in sock.gettimeout() which is
            # not exactly what we want and will skew the timeout :-(
            read_data = sock.recv(1)
        except socket.timeout:
            raise

        except SSLWantReadError:
            # We want to read data from the socket but got an SSL exception
            # try to read from the socket again
            #
            # This might skew the timeout because we wait two times for the
            # same call to _recv but should be just for some edge cases
            continue

        except socket.error as exc:
            error_code = extract_error_code(exc)

            if error_code is None:
                raise

            if error_code not in (errno.EAGAIN, errno.EWOULDBLOCK):
                # We want to read data from the socket but got an EAGAIN error
                # try to read from the socket again
                #
                # This might skew the timeout because we wait two times for the
                # same call to _recv but should be just for some edge cases
                continue
        else:
            if not read_data:
                # socket.recv() will return an empty string when the connection is
                # closed. Raise an exception
                raise WebSocketConnectionClosedException('Connection is already closed')

            data += read_data

    # timeout reached or all data read, return when we got from the wire
    return data
