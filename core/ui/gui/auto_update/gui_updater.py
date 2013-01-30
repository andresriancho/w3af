'''
gui_updater.py

Copyright 2007 Andres Riancho

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
import gtk

from core.ui.gui.constants import W3AF_ICON
from core.ui.gui import entries

from core.controllers.auto_update.version_manager import VersionMgr
from core.controllers.auto_update.ui_wrapper import UIUpdater


class GUIUpdater(UIUpdater):

    def __init__(self, force, log):

        def ask(msg):
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
            dlg.set_icon_from_file(W3AF_ICON)
            opt = dlg.run()
            dlg.destroy()
            return opt == gtk.RESPONSE_YES

        UIUpdater.__init__(self, force=force, ask=ask, logger=log)

        #  Event registration
        self._register(
            VersionMgr.ON_ACTION_ERROR,
            GUIUpdater.notify,
            'Error occurred.'
        )
        self._register(
            VersionMgr.ON_UPDATE_ADDED_DEP,
            GUIUpdater.notify,
            ('At least one new dependency was included in '
             'w3af. Please update manually.')
        )

    @staticmethod
    def notify(msg):
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, msg)
        dlg.set_icon_from_file(W3AF_ICON)
        dlg.run()
        dlg.destroy()

    def _handle_update_output(self, upd_output):
        if upd_output is not None:
            files, lrev, rrev = upd_output
            if rrev:
                tabnames = ("Updated Files", "Latest Changes")
                dlg = entries.TextDialog("Update report",
                                         tabnames=tabnames,
                                         icon=W3AF_ICON)
                dlg.add_message(str(files), page_num=0)
                dlg.add_message(str(self._vmngr.show_summary(lrev, rrev)),
                               page_num=1)
                dlg.done()
                dlg.dialog_run()

    def _log(self, msg):
        GUIUpdater.notify(msg)