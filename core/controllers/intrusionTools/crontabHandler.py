'''
crontabHandler.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''

import core.controllers.outputManager as om
from core.controllers.w3afException import *
from core.data.fuzzer.fuzzer import *
from core.controllers.intrusionTools.delayedExecution import delayedExecution
from core.controllers.intrusionTools.execMethodHelpers import *


class crontabHandler( delayedExecution ):
    '''
    This class defines a crontab handler, that will:
        - add new commands to the crontab calculating time
        - return expected execution time
        - restore old crontab
    '''

    def __init__( self, execMethod ):
        self._execMethod = execMethod
        self._cronFile = getRemoteTempFile( self._execMethod )
        
    def canDelay( self ):
        '''
        @return: True if the remote user can add entries to his crontab
        '''
        actualCron = self._exec( 'crontab -l 2>&1' )
        if 'not allowed to use this program' in actualCron:
            om.out.debug('[crontabHandler] The user has no permission to create a cron entry.')
            return False
        else:
            om.out.debug('[crontabHandler] The user can create a cron entry.')
            return True
            
    def addToSchedule( self, commandToExec ):
        '''
        Adds a command to the cron.
        '''
        actualCron = self._exec( 'crontab -l 2>&1' )
        actualCron = actualCron.strip()
        
        remoteDate = self._exec( 'date +%d-%m-%H:%M:%S-%u' )
        remoteDate = remoteDate.strip()
        
        user = self._exec( 'whoami')
        user = user.strip()
        
        newCronLine, waitTime = self._createCronLine( remoteDate, commandToExec )
        
        if 'no crontab for ' + user == actualCron:
            newCron = newCronLine
        else:
            newCron = actualCron + '\n' + newCronLine
        
        # This is done this way so I don't need to use one echo that prints new lines
        # new lines are \n and with gpc magic quotes that fails
        for line in newCron.split('\n'):
            self._exec( '/bin/echo ' + line + ' >> ' + self._cronFile )
        self._exec( 'crontab ' + self._cronFile )
        self._exec( '/bin/rm ' + self._cronFile )
        
        filename = commandToExec.split(' ')[0]
        self._exec( '/bin/chmod +x ' + filename )
        
        om.out.debug('Added command: "' + commandToExec + '" to the remote crontab of user : "'+user+'".')
        self._oldCron = actualCron
        
        return waitTime

    def restoreOldSchedule( self ):
        self._exec( '/bin/echo -e ' + self._oldCron + ' > ' + self._cronFile )
        self._exec( 'crontab ' + self._cronFile )
        self._exec( '/bin/rm ' + self._cronFile )
        om.out.debug('Successfully restored old crontab.')

    def _createCronLine( self, remoteDate, commandToExec ):
        '''
        Creates a crontab line that executes the command one minute after the "date" parameter.
        
        @return: A tuple with the new line to add to the crontab, and the time that it will take to run the command.
        '''
        resLine = ''
        try:
            # date +"%d-%m-%H:%M:%S-%u"
            dayNumber, month, hour, weekDay = remoteDate.split('-')
        except:
            raise w3afException('The date command of the remote server returned an unknown format.')
        else:
            hour, minute, sec = hour.split(':')
            waitTime = None
            if int(sec) > 57:
                # Just to be 100% sure...
                delta = 2
                waitTime = 4 + 60
            else:
                delta = 1
                waitTime = 60 - int(sec)
                
            minute = int( minute ) + delta
            hour, minute, amPm = self._fixTime( hour, minute )
            
            resLine = str( minute ) + ' ' + str(hour) + ' ' + str(dayNumber) + ' ' + str(month) + ' ' + str(weekDay) + ' ' + commandToExec
                
        return resLine, waitTime
