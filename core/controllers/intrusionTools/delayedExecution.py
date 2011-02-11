'''
delayedExecution.py

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

class delayedExecution:
    '''
    This class is a base class for crontabHandler and atHandler.
    '''

    def _exec( self, command ):
        '''
        A wrapper for executing commands
        '''
        om.out.debug('Executing: ' + command )
        response = apply( self._execMethod, ( command ,))
        om.out.debug('"' + command + '" returned: ' + response )
        return response
        
    def _fixTime( self, hour, minute, amPm='' ):
        '''
        Fix the time, this is done to fix if minute == 60, or ampm changes from am to pm, etc...
        '''
        hour = int(hour)
        minute = int(minute)
        
        if minute == 60:
            minute = 0
            hour = hour + 1
            return self._fixTime( hour, minute, amPm )
            
        if hour == 13 and amPm.startswith('a'):
            amPm = ''
            
        if hour == 24:
            hour = 0
            amPm = 'a'
            
        return hour, minute, amPm
