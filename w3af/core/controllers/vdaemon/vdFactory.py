"""
vdFactory.py

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
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.vdaemon.lnxVd import lnxVd
from w3af.core.controllers.vdaemon.winVd import winVd
from w3af.core.controllers.intrusion_tools.execMethodHelpers import os_detection_exec
from w3af.core.controllers.exceptions import BaseFrameworkException


def get_virtual_daemon(exec_method):
    """
    Uses the exec_method to run remote commands and determine what's the
    remote OS is, and based on that info, it returns the corresponding virtual
    daemon.
    """
    try:
        os = os_detection_exec(exec_method)
    except BaseFrameworkException, w3:
        raise w3
    else:
        if os == 'windows':
            om.out.debug(
                'Identified remote OS as Windows, returning winVd object.')
            return winVd(exec_method)
        elif os == 'linux':
            om.out.debug(
                'Identified remote OS as Linux, returning lnxVd object.')
            return lnxVd(exec_method)
        else:
            raise BaseFrameworkException(
                'Failed to get a virtual daemon for the remote OS: ' + os)
