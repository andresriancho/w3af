'''
exception_handler.py

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
import gtk

# w3af crash File creation
import tempfile
from core.data.fuzzer.fuzzer import createRandAlNum
import os

# w3af crash handling
from . import bug_report
from . import helpers
from core.controllers.misc.get_w3af_version import get_w3af_version


def handle_crash(type, value, tb, **data):
    '''Function to handle any exception that is not addressed explicitly.'''
    if issubclass(type, KeyboardInterrupt ):
        helpers.endThreads()
        import core.controllers.outputManager as om
        om.out.console(_('Thanks for using w3af.'))
        om.out.console(_('Bye!'))
        sys.exit(0)
        return
        
    exception = traceback.format_exception(type, value, tb)
    exception = "".join(exception)
    print exception

    # get version info for python, gtk and pygtk
    versions = _("\nPython version:\n%s\n\n") % sys.version
    versions += _("GTK version:%s\n") % ".".join(str(x) for x in gtk.gtk_version)
    versions += _("PyGTK version:%s\n\n") % ".".join(str(x) for x in gtk.pygtk_version)

    # get the version info for w3af
    versions += '\n' + get_w3af_version()

    # save the info to a file
    filename = tempfile.gettempdir() + os.path.sep + "w3af_crash-" + createRandAlNum(5) + ".txt"
    arch = file(filename, "w")
    arch.write(_('Submit this bug here: https://sourceforge.net/apps/trac/w3af/newticket \n'))
    arch.write(versions)
    arch.write(exception)
    arch.close()
    
    # Create the dialog that allows the user to send the bug to sourceforge
    
    bug_report_win = bug_report.bug_report_window(_('Bug detected!'), 
                                                  exception, versions,
                                                  filename, **data)
    
    # Blocks waiting for user interaction
    bug_report_win.show()
    
sys.excepthook = handle_crash
