"""
readMethodHelpers.py

Copyright 2010 Andres Riancho

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
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import OSDetectionException


def read_os_detection(remote_read):
    """
    Uses the remote_read method to read remote files and determine what the
    remote OS is.

    :return: String with 'windows' or 'linux' or raises a BaseFrameworkException
             if unknown.
    """
    try:
        linux1 = remote_read('/etc/passwd')
        linux2 = remote_read('/etc/mtab')
        linux3 = remote_read('/proc/sys/kernel/ostype')
    except BaseException:
        pass
    else:
        if '/bin/' in linux1 or 'rw' in linux2 or 'linux' in linux3.lower():
            om.out.debug('Identified remote OS as Linux, returning "linux".')
            return 'linux'

    try:
        # Try if it's a windows system
        # TODO: Are we sure that this works? When is the %SYSTEMROOT% resolved?
        win1 = remote_read('%SYSTEMROOT%\\win.ini')
        win2 = remote_read('C:\\windows\\win.ini')
        win3 = remote_read('C:\\win32\\win.ini')
        win4 = remote_read('C:\\win\\win.ini')
    except BaseException:
        pass
    else:
        if '[fonts]' in win1 + win2 + win3 + win4:
            om.out.debug(
                'Identified remote OS as Windows, returning "windows".')
            return 'windows'

    raise OSDetectionException('Failed to get/identify the remote OS.')
