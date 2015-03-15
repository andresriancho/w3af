"""
unhandled.py

Copyright 2009 Andres Riancho

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
import sys
import traceback

from functools import partial

import w3af.core.controllers.output_manager as om

from w3af.core.ui.gui import helpers
from w3af.core.ui.gui.exception_handling import unhandled_bug_report
from w3af.core.controllers.exception_handling.helpers import create_crash_file
from w3af.core.controllers.exception_handling.cleanup_bug_report import cleanup_bug_report


DEBUG_THREADS = False


def handle_crash(w3af_core, _type, value, tb, plugins=''):
    """Function to handle any exception that is not addressed explicitly."""
    if issubclass(_type, KeyboardInterrupt):
        handle_keyboardinterrupt(w3af_core)

    # Print the information to the console so everyone can see it
    exception = traceback.format_exception(_type, value, tb)
    exception = "".join(exception)
    print exception

    # Do not disclose user information in bug reports
    clean_exception = cleanup_bug_report(exception)

    # Save the info to a file for later analysis
    filename = create_crash_file(clean_exception)

    # Create the dialog that allows the user to send the bug to github
    bug_report_win = unhandled_bug_report.BugReportWindow(w3af_core,
                                                          _('Bug detected!'),
                                                          clean_exception,
                                                          filename, plugins)

    # Blocks waiting for user interaction
    bug_report_win.show()


def handle_keyboardinterrupt(w3af_core):
    # Kills some threads from the GUI, not from the core
    helpers.end_threads()
        
    w3af_core.quit()

    if DEBUG_THREADS:
        import threading
        import pprint
        
        def nice_thread_repr(alive_threads):
            repr_alive = [repr(x) for x in alive_threads]
            repr_alive.sort()
            return pprint.pformat(repr_alive)
        
        print nice_thread_repr(threading.enumerate())
        
    om.manager.set_output_plugins(['console'])
    om.out.console(_('\nStopping after Ctrl+C. Thanks for using w3af, bye!'))
    om.manager.process_all_messages()
     
    # 130 seems to be the correct exit code for this case
    # http://tldp.org/LDP/abs/html/exitcodes.html
    sys.exit(130)


def set_except_hook(w3af_core):
    sys.excepthook = partial(handle_crash, w3af_core)
