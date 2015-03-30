"""
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

"""
import gtk
import gobject
import threading

from w3af.core.ui.gui import helpers, entries
from w3af.core.ui.gui.reqResViewer import ReqResViewer
from w3af.core.ui.gui.tools.helpers.threaded_impact import ThreadedURLImpact

from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              ScanMustStopException,
                                              HTTPRequestException,
                                              ProxyException)

MANUAL_REQUEST_EXAMPLE = """\
GET http://w3af.org/ HTTP/1.1
Host: w3af.org
User-Agent: Firefox
"""


class ManualRequests(entries.RememberingWindow):
    """Infrastructure to generate manual HTTP requests.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af, initial_request=None):
        super(ManualRequests, self).__init__(w3af, "manualreq",
                                             "w3af - Manual Requests",
                                             "Manual_Requests")
        self.w3af = w3af
        
        #
        # Toolbar
        #
        self.send_but = entries.SemiStockButton(_("Send"), gtk.STOCK_MEDIA_PLAY,
                                                _("Send HTTP request"))
        self.send_but.connect("clicked", self._send)
        self.send_but.show()
        
        # Fix content length checkbox
        self._fix_content_len_cb = gtk.CheckButton('Fix content length header')
        self._fix_content_len_cb.set_active(True)
        self._fix_content_len_cb.show()
        
        # request-response viewer
        self.reqresp = ReqResViewer(w3af, [self.send_but.set_sensitive],
                                    withManual=False, editableRequest=True)
        self.reqresp.response.set_sensitive(False)
        
        self.vbox.pack_start(self.reqresp, True, True)
        self.vbox.pack_start(self._fix_content_len_cb, False, False)
        self.vbox.pack_start(self.send_but, False, False)
        
        # Add a default request
        if initial_request is None:
            self.reqresp.request.show_raw(MANUAL_REQUEST_EXAMPLE, '')
        else:
            initial_up, initial_dn = initial_request
            self.reqresp.request.show_raw(initial_up, initial_dn)

        # Show all!
        self.show()

    def _send(self, widg):
        """Actually sends the manual requests.

        :param widg: who sent the signal.
        """
        tsup, tlow = self.reqresp.request.get_both_texts()

        busy = gtk.gdk.Window(self.window, gtk.gdk.screen_width(),
                              gtk.gdk.screen_height(), gtk.gdk.WINDOW_CHILD,
                              0, gtk.gdk.INPUT_ONLY)
        busy.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        busy.show()

        while gtk.events_pending():
            gtk.main_iteration()

        # Get the fix content length value
        fix_content_len = self._fix_content_len_cb.get_active()

        # threading game
        event = threading.Event()

        impact = ThreadedURLImpact(self.w3af, tsup, tlow, event,
                                   fix_content_len)

        def impact_done():
            if not event.isSet():
                return True
            busy.destroy()

            if impact.ok:
                self.reqresp.response.set_sensitive(True)
                self.reqresp.response.show_object(impact.httpResp)
                self.reqresp.nb.next_page()
                
            elif hasattr(impact, 'exception'):
                known_exceptions = (BaseFrameworkException,
                                    ScanMustStopException,
                                    HTTPRequestException,
                                    ProxyException)
                if not isinstance(impact.exception, known_exceptions):
                    raise impact.exception
                else:
                    msg = "Stopped sending requests because of the following"\
                          " unexpected error:\n\n%s"

                    self.reqresp.response.clear_panes()
                    self.reqresp.response.set_sensitive(False)
                    gtk.gdk.threads_enter()
                    helpers.FriendlyExceptionDlg(msg % impact.exception)
                    gtk.gdk.threads_leave()

            else:
                # This is a very strange case, because impact.ok == False
                # but impact.exception does not exist!
                self.reqresp.response.clear_panes()
                self.reqresp.response.set_sensitive(False)
                gtk.gdk.threads_enter()
                helpers.FriendlyExceptionDlg('Errors occurred while sending'
                                             ' the HTTP request.')
                gtk.gdk.threads_leave()

            return False

        impact.start()
        gobject.timeout_add(200, impact_done)