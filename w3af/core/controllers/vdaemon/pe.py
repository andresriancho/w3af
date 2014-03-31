"""
pe.py

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
import os

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException


class pe(object):
    """
    This class represents a PE file.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, arch='32bit'):
        self._arch = arch
        self._shellcode = '\x90'
        self._maxPayloadLen = 1024
        self._templateFileName = os.path.join(ROOT_PATH, 'core', 'controllers',
                                              'vdaemon', 'pe_template.dat')

    def set_shell_code(self, sc):
        if len(sc) > self._maxPayloadLen:
            raise BaseFrameworkException('Payload to long!')
        self._shellcode = sc

    def get_shell_code(self):
        return self._shellcode

    def dump(self):
        """
        :return: A string with the complete pe file.
        """
        try:
            template = file(self._templateFileName, 'r').read()
        except Exception, e:
            raise BaseFrameworkException(
                'Failed to open PE template file. Exception: ' + str(e))
        else:
            paddingLen = self._maxPayloadLen - len(self._shellcode)
            executable = template.replace('\x90' * self._maxPayloadLen,
                                          self._shellcode + '\x90' * paddingLen)

        return executable
