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
import core.ui.consoleUi.io.console as term

from core.controllers.w3afException import *
from core.controllers.misc.get_w3af_version import get_w3af_version

# Provide a progress bar for all plugins.
from core.ui.consoleUi.progress_bar import progress_bar
import threading
import sys
import time

# This is to perform the "print scan status" in show_progress_on_request()
import select


class rootMenu(menu):
    '''
    Main menu
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, name, console, core, parent=None):
        menu.__init__(self, name, console, core, parent)
        self._loadHelp( 'root' )
        
        #   At first, there is no scan thread
        self._scan_thread = None
        
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
        # Check if the console output plugin is enabled or not, and warn.
        output_plugins = self._w3af.plugins.getEnabledPlugins('output')
        if 'console' not in output_plugins:
            msg = "Warning: You disabled the console output plugin. The scan information, such as"
            msg += ' discovered vulnerabilities won\'t be printed to the console, we advise you'
            msg += ' to enable this output plugin in order to be able to actually see'
            msg += ' the scan output in the console.'
            print msg
        
        self._scan_thread = threading.Thread(target=self._real_start)
        self._scan_thread.start()
        try:
            # let the core start
            time.sleep(1)
            if self._w3af.status.get_status() != 'Not running.':
                self.show_progress_on_request()
        except KeyboardInterrupt, k:
            om.out.console('User hit Ctrl+C, stopping scan.')
            time.sleep(1)
            self._w3af.stop()
            
    def _cmd_cleanup(self, params):
        '''
        The user runs this command, when he has finished a scan, and wants to cleanup everything to
        start a new scan to another target.
        
        @return: None
        '''
        self._w3af.cleanup()
 
    def _real_start(self):
        '''
        Actually run core.start()
        @return: None
        '''
        try:
            self._w3af.plugins.init_plugins()
            self._w3af.verifyEnvironment()
            self._w3af.start()
        except w3afException, w3:
            om.out.error(str(w3))
        except w3afMustStopException, w3:
            om.out.error(str(w3))
        except Exception:
            self._w3af.stop()
            raise
     
    def show_progress_on_request(self):
        '''
        When the user hits enter, show the progress
        '''
        while self._w3af.status.is_running():
            
            # Define some variables...
            rfds = []
            wfds = []
            efds = []
            hitted_enter = False

            # TODO: This if is terrible! I need to remove it!
            # read from sys.stdin with a 0.5 second timeout
            if sys.platform != 'win32':
                # linux
                rfds, wfds, efds = select.select( [sys.stdin], [], [], 0.5)
                if rfds:
                    if len(sys.stdin.readline()):
                        hitted_enter = True
            else:
                # windows
                import msvcrt
                time.sleep(0.3)
                if msvcrt.kbhit():
                    if term.read(1) in ['\n', '\r', '\r\n', '\n\r']:
                        hitted_enter = True
            
            # If something was written to sys.stdin, read it
            if hitted_enter:
                
                # change back to the previous state
                hitted_enter = False
                
                # Get the information
                progress = self._w3af.progress.get_progress()
                eta = self._w3af.progress.get_eta()
                
                # Create the message to print
                progress = str(progress * 100)
                progress = progress[:5] + ' ' + '%'
                msg = 'Status: ' + self._w3af.status.get_status() + '\n'
                msg += 'Current phase status: ' + progress + ' - ETA: %.2dd %.2dh %.2dm %.2ds' % eta
                
                # Print
                om.out.console( msg , newLine=True)
        
    def _cmd_version(self, params):
        '''
        Show the w3af version and exit
        '''
        om.out.console( get_w3af_version() )

    def join(self):
        '''
        Wait for the scan to properly finish.
        '''
        if self._scan_thread:
            self._scan_thread.join()
            #   After the scan finishes, there is no scan thread
            self._scan_thread = None
            
