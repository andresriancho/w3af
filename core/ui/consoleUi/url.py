'''
url.py

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

# Some traditional imports
import traceback
import sys

# Import w3af
import core.controllers.w3afCore
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.consoleUi.consoleMenu import consoleMenu
from core.ui.consoleUi.pluginConfig import pluginConfig

class url(consoleMenu):
    '''
    This is the url configuration menu for the console.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self, w3af, commands = [] ):
        consoleMenu.__init__(self)  
        self._w3af = w3af
        self._commands = commands
    
    def sh( self ):
        '''
        Starts the shell's main loop.
        
        @return: The prompt
        '''
        try:
            pConf = pluginConfig( self._w3af, self._commands )
            prompt = 'w3af/http-settings>>> '
            pConf.sh( prompt, self._w3af.uriOpener.settings )
        except KeyboardInterrupt:
            om.out.console( '' )
        return False
        


