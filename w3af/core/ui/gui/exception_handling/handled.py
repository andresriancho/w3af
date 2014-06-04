"""
handled.py

Copyright 2012 Andres Riancho

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
from w3af.core.controllers.exception_handling.helpers import gettempdir, create_crash_file
from w3af.core.ui.gui.exception_handling import handled_bug_report


def handle_exceptions(w3af_core):
    """
    In w3af's new exception handling method, some exceptions raising from
    plugins are "allowed" and the scan is NOT stopped because of them.

    At the same time, developers still want users to report their bugs.

    Because of that, we need to have a handler that at the end of the scan
    will allow the user to report the exceptions that were found during the
    scan.

    The main class in this game is core.controllers.core_helpers.exception_handler
    and you should read it before this one.
    """
    # Save the info to a file for later analysis by the user
    for edata in w3af_core.exception_handler.get_unique_exceptions():
        edata_str = edata.get_details()
        create_crash_file(edata_str)

    msg = 'Complete information related to the exceptions is available at "%s"'
    print msg % gettempdir()

    # We do this because it would be both awful and useless to simply
    # print all exceptions one below the other in the console
    print w3af_core.exception_handler.generate_summary_str()

    # Create the dialog that allows the user to send the bugs, potentially more
    # than one since we captured all of them during the scan using the new
    # exception_handler, to Github.
    title = _('Handled exceptions to report')
    bug_report_win = handled_bug_report.BugReportWindow(w3af_core, title)

    # Blocks waiting for user interaction
    bug_report_win.show()
