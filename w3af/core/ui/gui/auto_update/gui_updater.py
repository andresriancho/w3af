"""
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

"""
import gtk

from w3af.core.ui.gui.constants import W3AF_ICON
from w3af.core.ui.gui import entries

from w3af.core.controllers.auto_update.version_manager import VersionMgr
from w3af.core.controllers.auto_update.ui_wrapper import UIUpdater
from w3af.core.controllers.auto_update.utils import to_short_id, get_commit_id_date


def ask(msg):
    dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                            gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
    dlg.set_icon_from_file(W3AF_ICON)
    opt = dlg.run()
    dlg.destroy()
    return opt == gtk.RESPONSE_YES


def notify(msg):
    dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                            gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, msg)
    dlg.set_icon_from_file(W3AF_ICON)
    dlg.run()
    dlg.destroy()
        

class GUIUpdater(UIUpdater):

    def __init__(self, force, log):
        UIUpdater.__init__(self, force=force, ask=ask, logger=log)
        self._dot_counter = 1
        
        #  Event registration
        self._register(
            VersionMgr.ON_ACTION_ERROR,
            notify,
            _('Update error, please update manually.')
        )
        self._register(
            VersionMgr.ON_UPDATE_ADDED_DEP,
            notify,
            _('New dependencies added, please restart w3af.')
        )
        
        #
        # I register to this event because it will get called once every time
        # the git client has performed some progress, which is ideal for me to
        # give the user some feedback on the download progress.
        #
        # Also, and given that the Splash window was coded in a kind of messy
        # way, it's my chance to call the push method, which will call the
        # window's mainloop and help me keep the window alive
        #
        self._register(
            VersionMgr.ON_PROGRESS,
            self._downloading,
            None,
        )
    
    def _downloading(self, ignored_param):
        """
        :return:
            * Updating .
            * Updating ..
            * Updating ...
            * Updating ....
            
        And then start again,
        """
        d = self._dot_counter
        self._dot_counter = d + 1 if d < 3 else 1
        
        message = 'Updating %s' % ('.' * self._dot_counter)
        self._logger(message)
    
    def update(self):
        super(GUIUpdater, self).update()
    
    def _generate_report(self, changelog, local_commit_id, remote_commit_id):
        """
        :return: A string with a report of the latest update from local commit
                 to remote commit which changes stuff in changelog.
        """
        lshort = to_short_id(local_commit_id)
        rshort = to_short_id(remote_commit_id)
        ldate = get_commit_id_date(local_commit_id)
        rdate = get_commit_id_date(remote_commit_id)
        
        report = 'The following changes were applied to the local w3af'\
                 ' installation during the last update from %s (%s) to'\
                 ' %s (%s):\n\n%s'
        
        return report % (lshort, ldate, rshort, rdate, changelog)
    
    def _handle_update_output(self, upd_output):
        if upd_output is not None:
            
            changelog, local_commit_id, remote_commit_id = upd_output
            
            if changelog.get_changes():

                dlg = entries.TextDialog("Update report",
                                         icon=W3AF_ICON)
                dlg.add_message(self._generate_report(changelog,
                                                      local_commit_id,
                                                      remote_commit_id))
                dlg.done()
                dlg.dialog_run()

    def _log(self, msg):
        notify(msg)

