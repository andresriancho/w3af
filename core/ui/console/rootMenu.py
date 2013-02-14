'''
rootMenu.py

Copyright 2008 Andres Riancho

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

'''
import sys
import time
import select

from multiprocessing.dummy import Process

import core.controllers.output_manager as om
import core.ui.console.io.console as term

from core.ui.console.menu import menu
from core.ui.console.plugins import pluginsMenu
from core.ui.console.profiles import profilesMenu
from core.ui.console.exploit import exploit
from core.ui.console.config import configMenu
from core.ui.console.kbMenu import kbMenu
from core.ui.console.bug_report import bug_report_menu
from core.ui.console.util import mapDict
from core.ui.console.tables import table

from core.controllers.exceptions import w3afException, w3afMustStopException
from core.controllers.misc.get_w3af_version import get_w3af_version
from core.controllers.misc_settings import MiscSettings



class rootMenu(menu):
    '''
    Main menu
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    def __init__(self, name, console, core, parent=None):
        menu.__init__(self, name, console, core, parent)
        self._load_help('root')

        #   At first, there is no scan thread
        self._scan_thread = None

        mapDict(self.addChild, {
            'plugins': pluginsMenu,
            'target': (configMenu, self._w3af.target),
            'misc-settings': (configMenu, MiscSettings()),
            'http-settings': (configMenu, self._w3af.uri_opener.settings),
            'profiles': profilesMenu,
            'bug-report': bug_report_menu,
            'exploit': exploit,
            'kb': kbMenu
        })

    def _cmd_start(self, params):
        '''
        Start the core in a different thread, monitor keystrokes in the main thread.
        @return: None
        '''
        # Check if the console output plugin is enabled or not, and warn.
        output_plugins = self._w3af.plugins.get_enabled_plugins('output')
        if 'console' not in output_plugins:
            msg = "Warning: You disabled the console output plugin. If you"\
                  " start a new scan, the discovered vulnerabilities won\'t be"\
                  " printed to the console, we advise you to enable at least"\
                  " one output plugin in order to be able to actually see the"\
                  " the scan output."
            print msg

        # Note that I'm NOT starting this in a new multiprocess Process
        # please note the multiprocessing.dummy , this is required because
        # I want to start new threads inside this thread and there is a bug
        # with that http://bugs.python.org/issue10015
        self._scan_thread = Process(target=self._real_start)
        self._scan_thread.name = 'ConsoleScanThread'
        self._scan_thread.daemon = True
        self._scan_thread.start()
        
        # let the core thread start
        time.sleep(1)
        
        try:
            if self._w3af.status.get_status() != 'Not running.':
                self.show_progress_on_request()
        except KeyboardInterrupt:
            om.out.console('User pressed Ctrl+C, stopping scan.')
            self._w3af.stop()

    def _cmd_cleanup(self, params):
        '''
        The user runs this command, when he has finished a scan, and wants to
        cleanup everything to start a new scan to another target.

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
            self._w3af.verify_environment()
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
                rfds, wfds, efds = select.select([sys.stdin], [], [], 0.5)
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

                # Get the information and print it to the user
                status_information_str = self._w3af.status.get_long_status()
                t = table([(status_information_str,)])
                t.draw()
                om.out.console('')

    def _cmd_version(self, params):
        '''
        Show the w3af version and exit
        '''
        om.out.console(get_w3af_version())

    def join(self):
        '''
        Wait for the scan to properly finish.
        '''
        if self._scan_thread:
            self._scan_thread.join()
            #   After the scan finishes, there is no scan thread
            self._scan_thread = None
