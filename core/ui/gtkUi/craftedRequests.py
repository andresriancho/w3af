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
import core.ui.gtkUi.fuzzygen as fuzzygen
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
        self.reqresp = reqResViewer.reqResViewer([b])
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


class PreviewWindow(entries.RememberingWindow):
    '''A window with the analysis preview.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, pages):
        super(PreviewWindow,self).__init__(w3af, "fuzzypreview", "Preview")
        self.pages = pages
        # FIXME: make this modal!

        # content
        self.panes = reqResViewer.requestPaned()
        self.vbox.pack_start(self.panes.notebook)

        # the ok button
        centerbox = gtk.HBox()
        self.pagesControl = entries.PagesControl(self._pageChange, len(pages))
        centerbox.pack_start(self.pagesControl, True, False) 
        self.vbox.pack_start(centerbox, False, False, padding=5)

        self._pageChange(0)
        self.show_all()

    def _pageChange(self, page):
        print "page change!", page
        (txtup, txtdn) = self.pages[page]
        self.panes.rawShow(txtup, txtdn)



FUZZYHELP = """\
"$" is the delimiter
Use "$$" to include a "$"
"$something$" will eval "something" 
Already imported:
    the "string" module
    the "xx" function
"""

class FuzzyRequests(entries.RememberingWindow):
    '''Infrastructure to generate fuzzy HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(FuzzyRequests,self).__init__(w3af, "fuzzyreq", "w3af - Fuzzy Requests")
        self.w3af = w3af
        mainhbox = gtk.HBox()

        # ---- left pane ----
        vbox = gtk.VBox()
        mainhbox.pack_start(vbox)

        # we create the buttons first, to pass them
        analyzBut = gtk.Button("Analyze")
        sendBut = gtk.Button("Send all")

        # request and help
        hbox = gtk.HBox()
        self.originalReq = reqResViewer.requestPaned([analyzBut, sendBut])
        
        # Add a default request
        self.originalReq.rawShow(request_example, '')

        hbox.pack_start(self.originalReq.notebook, True, True)
        l = gtk.Label(FUZZYHELP)
        hbox.pack_start(l, False, False, padding=10)
        vbox.pack_start(hbox, True, True)

        # the commands
        t = gtk.Table(2, 3)
        analyzBut.connect("clicked", self._analyze)
        t.attach(analyzBut, 0, 1, 0, 1)
        self.analyzefb = gtk.Label("? requests")
        t.attach(self.analyzefb, 1, 2, 0, 1)
        self.preview = gtk.CheckButton("preview")
        t.attach(self.preview, 2, 3, 0, 1)
        sendBut.connect("clicked", self._send)
        t.attach(sendBut, 0, 1, 1, 2)
        self.sendfb = gtk.Label("? ok, ? errors")
        t.attach(self.sendfb, 1, 2, 1, 2)
        vbox.pack_start(t, False, False, padding=5)

        # ---- right pane ----
        vbox = gtk.VBox()
        mainhbox.pack_start(vbox)

        # result itself
        self.resultReqResp = reqResViewer.reqResViewer()
        self.resultReqResp.set_sensitive(False)
        vbox.pack_start(self.resultReqResp, True, True)

        # result control
        centerbox = gtk.HBox()
        self.pagesControl = entries.PagesControl(self._pageChange)
        centerbox.pack_start(self.pagesControl, True, False) 
        vbox.pack_start(centerbox, False, False, padding=5)

        # Show all!
        self.vbox.pack_start(mainhbox)
        self.show_all()

    def _analyze(self, widg):
        prev = self.preview.get_active()
        print "analyze! preview:", prev
        (request, postbody) = self.originalReq.getBothTexts()
        try:
            fg = helpers.coreWrap(fuzzygen.FuzzyGenerator, request, postbody)
        except fuzzygen.FuzzyError:
            return
            
        preview = list(fg.generate())
        self.analyzefb.set_text("%d requests" % len(preview))
        PreviewWindow(self.w3af, preview)


    def _send(self, widg):
        print "send!"

    def _pageChange(self, page):
        print "page changed:", page
