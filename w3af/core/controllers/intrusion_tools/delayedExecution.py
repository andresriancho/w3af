"""
delayedExecution.py

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


class delayedExecution(object):
    """
    This class is a base class for crontabHandler and atHandler.
    """
    def __init__(self, exec_method):
        self._exec_method = exec_method

    def _exec(self, command):
        """
        A wrapper for executing commands
        """
        om.out.debug('Executing: "%s".' % command)
        response = apply(self._exec_method, (command,))
        om.out.debug('"%s" returned "%s".' % (command, response) )
        
        return response

    def _fix_time(self, hour, minute, am_pm=''):
        """
        Fix the time, this is done to fix if minute == 60, or ampm changes
        from am to pm, etc...
        """
        hour = int(hour)
        minute = int(minute)

        if minute == 60:
            minute = 0
            hour = hour + 1
            return self._fix_time(hour, minute, am_pm)

        if hour == 13 and am_pm.startswith('a'):
            am_pm = ''

        if hour == 24:
            hour = 0
            am_pm = 'a'

        return hour, minute, am_pm
