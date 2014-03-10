"""
delayedExecutionFactory.py

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

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.intrusion_tools.execMethodHelpers import os_detection_exec
from w3af.core.controllers.intrusion_tools.crontabHandler import crontabHandler
from w3af.core.controllers.intrusion_tools.atHandler import atHandler


class delayedExecutionFactory(object):
    """
    This class constructs a delayedExecution based on the remote operating system.
    """
    def __init__(self, exec_method):
        self._exec_method = exec_method

    def get_delayed_execution_handler(self):
        os = os_detection_exec(self._exec_method)
        if os == 'windows':
            return atHandler(self._exec_method)
        elif os == 'linux':
            return crontabHandler(self._exec_method)
        else:
            raise BaseFrameworkException(
                'Failed to create a delayed execution handler.')
