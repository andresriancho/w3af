'''
unhandled.py

Copyright 2009 Andres Riancho

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

import sys
import traceback

from core.ui.gtkUi import helpers
from core.ui.gtkUi.exception_handling import unhandled_bug_report
from core.ui.gtkUi.exception_handling.helpers import pprint_plugins, create_crash_file
from core.data.misc.cleanup_bug_report import cleanup_bug_report 


def handle_crash(type, value, tb, plugins=''):
    '''Function to handle any exception that is not addressed explicitly.'''
    if issubclass(type, KeyboardInterrupt ):
        helpers.endThreads()
        import core.controllers.outputManager as om
        om.out.console(_('Thanks for using w3af.'))
        om.out.console(_('Bye!'))
        sys.exit(0)
        return
    
    # Print the information to the console so everyone can see it 
    exception = traceback.format_exception(type, value, tb)
    exception = "".join(exception)
    print exception

    # Do not disclose user information in bug reports
    clean_exception = cleanup_bug_report(exception)

    # Save the info to a file for later analysis
    filename = create_crash_file( clean_exception )
    
    # Create the dialog that allows the user to send the bug to Trac
    bug_report_win = unhandled_bug_report.bug_report_window( _('Bug detected!'), 
                                                             clean_exception,
                                                             filename, plugins)
    
    # Blocks waiting for user interaction
    bug_report_win.show()
    
sys.excepthook = handle_crash
