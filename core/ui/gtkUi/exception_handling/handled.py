'''
handled.py

Copyright 2012 Andres Riancho

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

import os
import sys
import traceback
import tempfile

from core.controllers.coreHelpers.exception_handler import exception_handler
from core.data.misc.cleanup_bug_report import cleanup_bug_report

from core.ui.gtkUi.exception_handling.helpers import gettempdir
from core.ui.gtkUi.exception_handling import handled_bug_report



def handle_exceptions(enabled_plugins=''):
    '''
    In w3af's new exception handling method, some exceptions raising from
    plugins are "allowed" and the scan is NOT stopped because of them.
    
    At the same time, developers still want users to report their bugs.
    
    Because of that, we need to have a handler that at the end of the scan
    will allow the user to report the exceptions that were found during the
    scan.
    
    The main class in this game is core.controllers.coreHelpers.exception_handler
    and you should read it before this one.
    '''    
    for exception in exception_handler.get_all_exceptions():
        
        # Save the info to a file for later analysis by the user
        exception_str = str(exception)

        # Do not disclose user information in bug reports
        clean_exception = cleanup_bug_report(exception_str)
        
        filename = create_crash_file(clean_exception)
    
    # We do this because it would be both awful and useless to simply
    # print all exceptions one below the other in the console
    print exception_handler.generate_summary_str()
    print 'Complete information related to the exceptions is available at "%s"' % gettempdir()
    
    # Create the dialog that allows the user to send the bugs, potentially more
    # than one since we captured all of them during the scan using the new
    # exception_handler, to Trac.
    bug_report_win = handled_bug_report.bug_report_window( _('Bug detected!'),
                                                           clean_exception,
                                                           enabled_plugins)
    
    # Blocks waiting for user interaction
    bug_report_win.show()

