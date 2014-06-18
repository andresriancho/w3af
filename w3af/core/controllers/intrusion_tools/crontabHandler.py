"""
crontabHandler.py

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
from w3af.core.controllers.intrusion_tools.execMethodHelpers import get_remote_temp_file


class crontabHandler(delayedExecution):
    """
    This class defines a crontab handler, that will:
        - add new commands to the crontab calculating time
        - return expected execution time
        - restore old crontab
    """

    def __init__(self, exec_method):
        super(crontabHandler, self).__init__(exec_method)
        self._cronFile = get_remote_temp_file(self._exec_method)

    def can_delay(self):
        """
        :return: True if the remote user can add entries to his crontab
        """
        actualCron = self._exec('crontab -l 2>&1')
        if 'not allowed to use this program' in actualCron:
            om.out.debug('[crontabHandler] The user has no permission to create a cron entry.')
            return False
        else:
            om.out.debug('[crontabHandler] The user can create a cron entry.')
            return True

    def add_to_schedule(self, command_to_exec):
        """
        Adds a command to the cron.
        """
        actualCron = self._exec('crontab -l 2>&1')
        actualCron = actualCron.strip()

        remoteDate = self._exec('date +%d-%m-%H:%M:%S-%u')
        remoteDate = remoteDate.strip()

        user = self._exec('whoami')
        user = user.strip()

        newCronLine, wait_time = self._createCronLine(
            remoteDate, command_to_exec)

        if 'no crontab for ' + user == actualCron:
            newCron = newCronLine
        else:
            newCron = actualCron + '\n' + newCronLine

        # This is done this way so I don't need to use one echo that prints new lines
        # new lines are \n and with gpc magic quotes that fails
        for line in newCron.split('\n'):
            self._exec('/bin/echo ' + line + ' >> ' + self._cronFile)
        self._exec('crontab ' + self._cronFile)
        self._exec('/bin/rm ' + self._cronFile)

        filename = command_to_exec.split(' ')[0]
        self._exec('/bin/chmod +x ' + filename)

        om.out.debug('Added command: "' + command_to_exec +
                     '" to the remote crontab of user : "' + user + '".')
        self._oldCron = actualCron

        return wait_time

    def restore_old_schedule(self):
        self._exec('/bin/echo -e ' + self._oldCron + ' > ' + self._cronFile)
        self._exec('crontab ' + self._cronFile)
        self._exec('/bin/rm ' + self._cronFile)
        om.out.debug('Successfully restored old crontab.')

    def _createCronLine(self, remoteDate, command_to_exec):
        """
        Creates a crontab line that executes the command one minute after the
        "date" parameter.

        :return: A tuple with the new line to add to the crontab, and the time
                 that it will take to run the command.
        """
        res_line = ''
        try:
            # date +"%d-%m-%H:%M:%S-%u"
            day_number, month, hour, week_day = remoteDate.split('-')
        except:
            raise BaseFrameworkException('The date command of the remote server returned an unknown format.')
        else:
            hour, minute, sec = hour.split(':')
            wait_time = None
            if int(sec) > 57:
                # Just to be 100% sure...
                delta = 2
                wait_time = 4 + 60
            else:
                delta = 1
                wait_time = 60 - int(sec)

            minute = int(minute) + delta
            hour, minute, am_pm = self._fix_time(hour, minute)

            res_line = '%s %s %s %s %s %s' % (minute, hour, day_number, month,
                                             week_day, command_to_exec)
            
        return res_line, wait_time
