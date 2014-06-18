"""
reverseFTP.py

Copyright 2006 Andres Riancho

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

from w3af.core.controllers.payload_transfer.base_payload_transfer import BasePayloadTransfer


class ReverseFTP(BasePayloadTransfer):
    """
    This is a class that defines how to send a file to a remote server a reverse
    connection and a ftp like transfer mode ( using a new TCP connection and
    socket.send/socket.recv )
    """

    def __init__(self, exec_method, os, inboundPort):
        super(ReverseFTP, self).__init__(exec_method, os)
        self._exec_method = exec_method
        self._os = os
        self._inbound_port = inboundPort

    def can_transfer(self):
        """
        This method is used to test if the transfer method works as expected.
        The implementation of this should transfer 10 bytes and check if they
        arrived as expected to the other end.
        """
        return False

    def estimate_transfer_time(self, size):
        """
        :return: An estimated transfer time for a file with the specified size.
        """
        return int(3)

    def _serve(self, data_str):
        """
        Listens for 1 connection on the inbound port, transfers the data and
        then returns. This function should be called with tm.apply_async ; and
        afterwards you should exec the ftp client on the remote server.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', self._inbound_port))
        server_socket.listen(1)

        client_socket, addr = server_socket.accept()

        #pylint: disable=E1101
        client_socket.send(data_str)
        client_socket.close()

        return True

    def transfer(self, data_str, destination):
        """
        This method is used to transfer the data_str from w3af to the
        compromised server. Steps:
            - using EchoLinux / EchoWindows transfer the reverseFTPClient.py
              file (or the cx_freezed version)
            - start the _serve method
            - call the reverseFTPClient.py file on the remote server using:
                - reverseFTPClient.py <w3af-ip-address> <port> <destination>
            - verify that the file exists
        """
        return False

    def get_speed(self):
        """
        :return: The transfer speed of the transfer object. It should return
                 a number between 100 (fast) and 1 (slow)
        """
        # Not as fast as ClientlessReverseHTTP or ClientlessReverseTFTP, just
        # because I need to upload a "ftp" client to the compromised host in
        # order to upload all the data afterwards.
        return 80
