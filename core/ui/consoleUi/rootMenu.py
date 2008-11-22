'''
rootMenu.py

Copyright 2008 Andres Riancho

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

from core.ui.consoleUi.menu import *
from core.ui.consoleUi.plugins import *
from core.ui.consoleUi.profiles import *
from core.ui.consoleUi.exploit import *
from core.ui.consoleUi.kbMenu import *
import core.controllers.miscSettings as ms
#from core.ui.consoleUi.session import *
from core.ui.consoleUi.util import *

from core.controllers.w3afException import *

# Provide a progress bar for all plugins.
from core.ui.consoleUi.progress_bar import progress_bar
import threading
import sys
import time
import select

class rootMenu(menu):
    '''
    Main menu
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, name, console, core, parent=None):
        menu.__init__(self, name, console, core, parent)
        self._loadHelp( 'root' )

        mapDict(self.addChild, {
            'plugins': pluginsMenu,
            'target' : (configMenu, self._w3af.target),
            'misc-settings' : (configMenu, ms.miscSettings()),
            'http-settings' : (configMenu, self._w3af.uriOpener.settings),
            'profiles' : profilesMenu,
            'exploit' : exploit,
            'kb': kbMenu
        })
       
    def _cmd_start(self, params):
        '''
        Start the core in a different thread, monitor keystrokes in the main thread.
        @return: None
        '''
        threading.Thread(target=self._real_start).start()
        try:
            # let the core start
            time.sleep(1)
            if self._w3af.getCoreStatus() != 'Not running.':
                self.show_progress_on_request()
        except KeyboardInterrupt, k:
            self._w3af.stop()
            om.out.console('User hitted Ctrl+C, stopping scan.')
            time.sleep(1)
 
    def _real_start(self):
        '''
        Actually run core.start()
        @return: None
        '''
        try:
            self._w3af.initPlugins()
            self._w3af.verifyEnvironment()
            self._w3af.start()
        except w3afException, w3:
            om.out.error(str(w3))
        except w3afMustStopException, w3:
            om.out.error(str(w3))
        except Exception, e:
            raise e
     
    def show_progress_on_request(self):
        '''
        When the user hits enter, show the progress
        '''
        while self._w3af.isRunning():
            # read from sys.stdin with a 0.5 second timeout
            rfds, wfds, efds = select.select( [sys.stdin], [], [], 0.5)
            
            # If something was written to sys.stdin, read it
            if rfds:
                # Get the information
                rfds[0].readline()
                progress = self._w3af.progress.get_progress()
                
                # Print
                om.out.console('Status: ' + self._w3af.getCoreStatus(), newLine=True)
                progress = str(progress * 100)
                progress = progress[:5] + ' ' + '%'
                om.out.console('Current phase status: ' + progress, newLine=True)
        
    def _cmd_version(self, params):
        '''
        Show the w3af version and exit
        '''
        om.out.console( self._w3af.getVersion() )
