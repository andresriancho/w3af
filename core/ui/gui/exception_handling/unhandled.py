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

from functools import partial

from core.ui.gui import helpers
from core.ui.gui.exception_handling import unhandled_bug_report
from core.controllers.exception_handling.helpers import create_crash_file
from core.controllers.exception_handling.cleanup_bug_report import cleanup_bug_report


def handle_crash(w3af_core, _type, value, tb, plugins=''):
    '''Function to handle any exception that is not addressed explicitly.'''
    if issubclass(_type, KeyboardInterrupt):
        helpers.endThreads()
        import core.controllers.output_manager as om
        om.out.set_output_plugins(['console'])
        om.out.console(_('\nStopping after Ctrl+C. Thanks for using w3af.'))
        om.out.console(_('Bye!'))
        om.out.process_all_messages()
        sys.exit(0)
        return

    # Print the information to the console so everyone can see it
    exception = traceback.format_exception(_type, value, tb)
    exception = "".join(exception)
    print exception

    # Do not disclose user information in bug reports
    clean_exception = cleanup_bug_report(exception)

    # Save the info to a file for later analysis
    filename = create_crash_file(clean_exception)

    # Create the dialog that allows the user to send the bug to Trac
    bug_report_win = unhandled_bug_report.bug_report_window(w3af_core,
                                                            _('Bug detected!'),
                                                            clean_exception,
                                                            filename, plugins)

    # Blocks waiting for user interaction
    bug_report_win.show()


def set_except_hook(w3af_core):
    sys.excepthook = partial(handle_crash, w3af_core)
