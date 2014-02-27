"""
main.py

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
from w3af.core.data.db.startup_cfg import StartUpConfig
from w3af.core.data.constants.disclaimer import DISCLAIMER


def ask(msg):
    dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                            gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
    dlg.set_icon_from_file(W3AF_ICON)
    opt = dlg.run()
    dlg.destroy()
    return opt == gtk.RESPONSE_YES


class DisclaimerController(object):
    def accept_disclaimer(self):
        """
        :return: True/False depending on the user's answer to our disclaimer.
                 Please note that in w3af_gui we'll stop if the user does
                 not accept the disclaimer.
        """
        startup_cfg = StartUpConfig()

        if startup_cfg.accepted_disclaimer:
            return True


        QUESTION = 'Do you accept the terms and conditions?'
        msg = DISCLAIMER + '\n\n' + QUESTION
        user_response = ask(msg)

        if user_response:
            startup_cfg.accepted_disclaimer = True
            startup_cfg.save()
            return True

        return False