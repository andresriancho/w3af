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
import core.ui.gtkUi.reqResViewer as reqResViewer
import core.ui.gtkUi.helpers as helpers
import core.ui.gtkUi.entries as entries
from core.controllers.w3afException import w3afException

request_example = """\
GET http://www.some_host.com/path HTTP/1.0
Host: www.some_host.com
User-Agent: w3af.sf.net
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
"""

class ManualRequests(entries.RememberingWindow):
    '''Infrastructure to generate manual HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(ManualRequests,self).__init__(w3af, "manualreq", "w3af - Manual Requests")
        self.w3af = w3af

        # send button
        hbox = gtk.HBox()
        b = gtk.Button("   Send   ")
        b.connect("clicked", self._send)
        hbox.pack_start(b, True, False)

        # request-response viewer
        self.reqresp = reqResViewer.reqResViewer(b)
        self.reqresp.response.notebook.set_sensitive(False)
        self.vbox.pack_start(self.reqresp, True, True)

        self.vbox.pack_start(hbox, False, False, padding=10)
        
        # Add a default request
        self.reqresp.request.rawShow(request_example, '')
        
        # Show all!
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
            self.reqresp.response.notebook.set_sensitive(False)
            return

        # get the info
        body = httpResp.getBody()
        headers = httpResp.dumpResponseHead()

        # activate and show
        self.reqresp.response.notebook.set_sensitive(True)
        self.reqresp.response.rawShow(headers, body)


class FuzzyRequests(entries.RememberingWindow):
    '''Infrastructure to generate fuzzy HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(FuzzyRequests,self).__init__(w3af, "fuzzyreq", "w3af - Fuzzy Requests")
        self.w3af = w3af

        # request and help
        hbox = gtk.HBox()
        self.originalReq = reqResViewer.requestPaned()
        hbox.pack_start(self.originalReq.notebook, True, True)
        l = gtk.Label("the help!")
        hbox.pack_start(l, True, True)
        self.vbox.pack_start(hbox, True, True)

        # the commands
        t = gtk.Table(2, 3)
        b = gtk.Button("Analyze")
        t.attach(b, 0, 1, 0, 1)
        self.analyzefb = gtk.Label("? requests")
        t.attach(self.analyzefb, 1, 2, 0, 1)
        self.preview = gtk.CheckButton("preview")
        t.attach(self.preview, 2, 3, 0, 1)
        b = gtk.Button("Send all")
        t.attach(b, 0, 1, 1, 2)
        self.sendfb = gtk.Label("? ok, ? errors")
        t.attach(self.sendfb, 1, 2, 1, 2)
        self.vbox.pack_start(t, padding=10)

        # result control
        hbox = gtk.HBox()
        b = gtk.Button()
        b.add(gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_OUT))
        hbox.pack_start(b)
        self.pageentry = gtk.Entry()
        hbox.pack_start(self.pageentry)
        b = gtk.Button()
        b.add(gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_OUT))
        hbox.pack_start(b)
        self.vbox.pack_start(hbox, padding=10)

        # result itself
        self.resultReqResp = reqResViewer.reqResViewer()
        self.vbox.pack_start(self.resultReqResp, True, True)

        # Show all!
        self.show_all()

