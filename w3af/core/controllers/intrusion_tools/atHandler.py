"""
atHandler.py

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
from w3af.core.controllers.intrusion_tools.delayedExecution import delayedExecution


class atHandler(delayedExecution):
    """
    This class defines an "at" handler, that will:
        - add new commands to the crontab calculating time
        - return expected execution time
        - restore old crontab
    """

    def __init__(self, exec_method):
        super(atHandler, self).__init__(exec_method)
        self._exec_method = exec_method

    def can_delay(self):
        """
        :return: True if the remote user can add entries to his crontab
        """
        om.out.debug('[atHandler] Verifying if the remote user can run the at command.')
        res = self._exec('at')

        if 'Access is denied' in res:
            return False
        else:
            return True

    def add_to_schedule(self, command_to_exec):
        """
        Adds a command to the cron.
        """
        # Save this for later
        self._filename = command_to_exec.split(' ')[0]

        # Work
        remoteTime = self._exec('time')
        atCommand, wait_time = self._create_at_command(remoteTime, command_to_exec)

        # Schedule the shellcode for execution
        self._exec(atCommand)
        om.out.debug(
            '[atHandler] Shellcode successfully added to "at" service.')

        return wait_time

    def restore_old_schedule(self):
        try:
            taskList = self._exec('at')
            for line in taskList.split('\n'):
                if self._filename in line:
                    taskId = line.split()[1]
                    break

            self._exec('at ' + taskId + ' /delete')
        except:
            om.out.debug('Failed to remove task from "at" service.')

    def _create_at_command(self, time, command):
        """
        Creates an at command based on the time and command parameter.

        This is the format i'm expecting for the time parameter:

        The current time is: 11:24:19.59
        Enter the new time:

        :return: A tuple with the "at" command, and the time that it will take
                 to run the command.
        """
        res = 'at '
        try:
            time = time.split('\n')[0].split(':')[1:]
            hour = time[0]
            minute = time[1]
            if '.' in time[2]:
                # windows 2k
                seconds = time[2].split('.')[0]
            else:
                # windows XP. This assholes reimplement the time command from
                # one release to another...
                seconds = time[2].split(',')[0]

            # TODO ( see below )
            if int(hour) > 12:
                am_pm = ''
            else:
                # TODO !
                # analyze... before I had am_pm = 'a' ; check if this is really necesary
                am_pm = ''
        except:
            raise BaseFrameworkException('The time command of the remote server returned an unknown format.')
        else:

            if int(seconds) > 57:
                # Just to be 100% sure...
                delta = 2
                wait_time = 60 + 5
            else:
                delta = 1
                wait_time = 60 - int(seconds)

            minute = int(minute) + delta
            hour, minute, am_pm = self._fix_time(hour, minute, am_pm)

            res += str(
                hour) + ':' + str(minute).zfill(2) + am_pm + ' ' + command

        return res, wait_time
