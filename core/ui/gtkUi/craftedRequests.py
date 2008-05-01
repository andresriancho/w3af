'''
craftedRequests.py

Copyright 2007 Andres Riancho

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

import pygtk, gtk
from core.ui.gtkUi.reqResViewer import reqResViewer
import core.ui.gtkUi.helpers as helpers
from core.controllers.w3afException import w3afException

class ManualRequests(gtk.Window):
    '''Infrastructure to generate manual HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(ManualRequests,self).__init__(gtk.WINDOW_TOPLEVEL)
        self.w3af = w3af

        # title, position and dimensions
        self.set_title("w3af - Manual Requests")
        self.winconfig = w3af.mainwin.generalconfig
        self.connect("delete_event", self.quit)
        self.resize(*self.winconfig.get("manualreq-size", (800, 600)))
        self.move(*self.winconfig.get("manualreq-position", (50, 50)))

        # main vertical box
        vbox = gtk.VBox()
        self.add(vbox)

        # send button
        hbox = gtk.HBox()
        b = gtk.Button("   Send   ")
        b.connect("clicked", self._send)
        hbox.pack_start(b, True, False)

        # request-response viewer
        self.reqresp = reqResViewer(b)
        self.reqresp.resultNotebook.set_sensitive(False)
        vbox.pack_start(self.reqresp, True, True)

        vbox.pack_start(hbox, False, False, padding=10)
        self.show_all()

    def _send(self, widg):
        '''Actually generates the manual requests.

        @param widget: who sent the signal.
        '''
        (tsup, tlow) = self.reqresp.request.getBothTexts()

        try:
            httpResp = helpers.coreWrap(self.w3af.uriOpener.sendRawRequest, tsup, tlow)
        except w3afException:
            self.reqresp.response.clearPanes()
            self.reqresp.resultNotebook.set_sensitive(False)
            return

        # get the info
        body = httpResp.getBody()
        headers = httpResp.dumpResponseHead()

        # activate and show
        self.reqresp.resultNotebook.set_sensitive(True)
        self.reqresp.response.rawShow(body, headers)

    def quit(self, widget, event):
        '''Windows quit, saves the position and size.

        @param widget: who sent the signal.
        @param event: the event that happened
        '''
        self.winconfig["manualreq-size"] = self.get_size()
        self.winconfig["manualreq-position"] = self.get_position()
        return False

