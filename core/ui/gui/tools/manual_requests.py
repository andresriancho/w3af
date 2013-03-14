'''
manual_requests.py

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
import gobject
import threading

from core.ui.gui import reqResViewer, helpers, entries
from core.ui.gui.tools.helpers import ThreadedURLImpact

from core.controllers.exceptions import (w3afException, w3afMustStopException,
                                         w3afMustStopOnUrlError,
                                         w3afMustStopByKnownReasonExc,
                                         w3afProxyException)

MANUAL_REQUEST_EXAMPLE = """\
GET http://localhost/script.php HTTP/1.0
Host: www.some_host.com
User-Agent: w3af.org
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
"""

UI_MENU = """
<ui>
  <toolbar name="Toolbar">
    <toolitem action="Send"/>
    <separator name="sep1"/>
  </toolbar>
</ui>
"""

class ManualRequests(entries.RememberingWindow):
    '''Infrastructure to generate manual HTTP requests.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, initialRequest=None):
        super(ManualRequests, self).__init__(w3af, "manualreq", "w3af - Manual Requests",
                                             "Manual_Requests")
        self.w3af = w3af
        self._uimanager = gtk.UIManager()
        accelgroup = self._uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')
        actiongroup.add_actions([
            ('Send', gtk.STOCK_YES, _('_Send Request'), None,
             _('Send request'), self._send),
        ])
        # Finish the toolbar
        self._uimanager.insert_action_group(actiongroup, 0)
        self._uimanager.add_ui_from_string(UI_MENU)
        toolbar = self._uimanager.get_widget('/Toolbar')
        b = toolbar.get_nth_item(0)
        self.vbox.pack_start(toolbar, False)
        toolbar.show()
        # Fix content length checkbox
        self._fix_content_lengthCB = gtk.CheckButton('Fix content length header')
        self._fix_content_lengthCB.set_active(True)
        self._fix_content_lengthCB.show()
        # request-response viewer
        self.reqresp = reqResViewer.reqResViewer(w3af, [b.set_sensitive],
                                                 withManual=False, editableRequest=True)
        self.reqresp.response.set_sensitive(False)
        self.vbox.pack_start(self._fix_content_lengthCB, False, False)
        self.vbox.pack_start(self.reqresp, True, True)
        # Add a default request
        if initialRequest is None:
            self.reqresp.request.show_raw(MANUAL_REQUEST_EXAMPLE, '')
        else:
            (initialUp, initialDn) = initialRequest
            self.reqresp.request.show_raw(initialUp, initialDn)

        # Show all!
        self.show()

    def _send(self, widg):
        '''Actually generates the manual requests.

        :param widget: who sent the signal.
        '''
        (tsup, tlow) = self.reqresp.request.get_both_texts()

        busy = gtk.gdk.Window(self.window, gtk.gdk.screen_width(),
                              gtk.gdk.screen_height(), gtk.gdk.WINDOW_CHILD,
                              0, gtk.gdk.INPUT_ONLY)
        busy.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        busy.show()

        while gtk.events_pending():
            gtk.main_iteration()

        # Get the fix content length value
        fixContentLength = self._fix_content_lengthCB.get_active()

        # threading game
        event = threading.Event()
        impact = ThreadedURLImpact(self.w3af, tsup, tlow, event,
                                   fixContentLength)

        def impact_done():
            if not event.isSet():
                return True
            busy.destroy()

            if impact.ok:
                self.reqresp.response.set_sensitive(True)
                self.reqresp.response.show_object(impact.httpResp)
                self.reqresp.nb.next_page()
            elif hasattr(impact, 'exception'):
                e_kls = impact.exception.__class__
                if e_kls in (w3afException, w3afMustStopException,
                             w3afMustStopOnUrlError,
                             w3afMustStopByKnownReasonExc,
                             w3afProxyException):
                    msg = "Stopped sending requests because '%s'" % str(
                        impact.exception)
                else:
                    raise impact.exception
                self.reqresp.response.clear_panes()
                self.reqresp.response.set_sensitive(False)
                gtk.gdk.threads_enter()
                helpers.friendlyException(msg)
                gtk.gdk.threads_leave()
            else:
                # This is a very strange case, because impact.ok == False
                # but impact.exception does not exist!
                self.reqresp.response.clear_panes()
                self.reqresp.response.set_sensitive(False)
                gtk.gdk.threads_enter()
                helpers.friendlyException(
                    'Errors occurred while sending the HTTP request.')
                gtk.gdk.threads_leave()

            return False

        impact.start()
        gobject.timeout_add(200, impact_done)