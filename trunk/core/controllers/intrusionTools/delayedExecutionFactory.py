'''
delayedExecutionFactory.py

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
from core.controllers.intrusionTools.execMethodHelpers import *

from core.controllers.intrusionTools.crontabHandler import crontabHandler
from core.controllers.intrusionTools.atHandler import atHandler

class delayedExecutionFactory:
    '''
    This class constructs a delayedExecution based on the remote operating system.
    '''
    def __init__( self, execMethod ):
        self._execMethod = execMethod
        
    def getDelayedExecutionHandler( self ):
        os = osDetectionExec( self._execMethod )
        if os == 'windows':
            return atHandler( self._execMethod )
        elif os == 'linux':
            return crontabHandler( self._execMethod )
        else:
            raise w3afException('Failed to create a delayed execution handler.')
            

