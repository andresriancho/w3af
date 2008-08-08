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

import gtk, gobject, threading
from . import reqResViewer, helpers, entries, fuzzygen

# Alternative ways of seeing the data
from .clusterGraph import clusterGraphWidget

from core.controllers.w3afException import w3afException, w3afMustStopException 
import os

request_example = """\
GET http://localhost/path HTTP/1.0
Host: www.some_host.com
User-Agent: w3af.sf.net
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
"""

class ThreadedURLImpact(threading.Thread):
    '''Impacts an URL in a different thread.'''
    def __init__(self, w3af, tsup, tlow, event, fixContentLength):
        self.tsup = tsup
        self.tlow = tlow
        self.w3af = w3af
        self.event = event
        self.ok = False
        self.fixContentLength = fixContentLength
        threading.Thread.__init__(self)

    def run(self):
        '''Starts the thread.'''
        try:
            self.httpResp = self.w3af.uriOpener.sendRawRequest(self.tsup, self.tlow, self.fixContentLength)
            self.ok = True
        except Exception, e:
            self.exception = e
        finally:
            self.event.set()
            

class ManualRequests(entries.RememberingWindow):
    '''Infrastructure to generate manual HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, initialRequest=None):
        super(ManualRequests,self).__init__(w3af, "manualreq", "w3af - Manual Requests")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af

        # The table to store the checkbox and the button
        table = gtk.Table(1, 20)
        table.set_col_spacings(10)
        
        # Fix content length checkbox
        self._fixContentLengthCB = gtk.CheckButton('Fix content length header')
        self._fixContentLengthCB.set_active(True)
        self._fixContentLengthCB.show()

        # send button
        b = gtk.Button("   Send   ")
        b.connect("clicked", self._send)
        
        # Store all inside the table
        table.attach(self._fixContentLengthCB, 9, 10, 0, 1, xoptions=gtk.SHRINK)
        table.attach(b, 19, 20, 0, 1, xoptions=gtk.SHRINK)

        # request-response viewer
        self.reqresp = reqResViewer.reqResViewer(w3af, [b], withManual=False, editableRequest=True)
        self.reqresp.response.set_sensitive(False)
        self.vbox.pack_start(self.reqresp, True, True)

        self.vbox.pack_start(table, False, False)
        
        # Add a default request
        if initialRequest is None:
            self.reqresp.request.rawShow(request_example, '')
        else:
            (initialUp, initialDn) = initialRequest
            self.reqresp.request.rawShow(initialUp, initialDn)
        
        # Show all!
        table.show_all()
        self.show()

    def _send(self, widg):
        '''Actually generates the manual requests.

        @param widget: who sent the signal.
        '''
        (tsup, tlow) = self.reqresp.request.getBothTexts()

        busy = gtk.gdk.Window(self.window, gtk.gdk.screen_width(), gtk.gdk.screen_height(), gtk.gdk.WINDOW_CHILD, 0, gtk.gdk.INPUT_ONLY)
        busy.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        busy.show()
        while gtk.events_pending():
            gtk.main_iteration()

        # Get the fix content length value
        fixContentLength = self._fixContentLengthCB.get_active()

        # threading game
        event = threading.Event()
        impact = ThreadedURLImpact(self.w3af, tsup, tlow, event, fixContentLength)
        def impactDone():
            if not event.isSet():
                return True
            busy.destroy()

            if impact.ok:
                self.reqresp.response.set_sensitive(True)
                self.reqresp.response.showObject(impact.httpResp)
            else:
                if impact.exception.__class__ == w3afException:
                    msg = str(impact.exception)
                elif impact.exception.__class__ == w3afMustStopException:
                    msg = "Stopped sending requests because " + str(impact.exception)
                else:
                    raise impact.exception
                self.reqresp.response.clearPanes()
                self.reqresp.response.set_sensitive(False)
                gtk.gdk.threads_enter()
                helpers.friendlyException(msg)
                gtk.gdk.threads_leave()

            return False

        impact.start()
        gobject.timeout_add(200, impactDone)


class PreviewWindow(entries.RememberingWindow):
    '''A window with the analysis preview.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, parent, pages):
        super(PreviewWindow,self).__init__(w3af, "fuzzypreview", "Preview")
        self.pages = pages
        self.set_modal(True)
        self.set_transient_for(parent) 

        # content
        self.panes = reqResViewer.requestPaned(w3af, editable=False, widgname="fuzzypreview")
        self.vbox.pack_start(self.panes.notebook)

        # the ok button
        centerbox = gtk.HBox()
        self.pagesControl = entries.PagesControl(w3af, self._pageChange, len(pages))
        centerbox.pack_start(self.pagesControl, True, False) 
        self.vbox.pack_start(centerbox, False, False, padding=5)

        self._pageChange(0)
        self.show_all()

    def _pageChange(self, page):
        (txtup, txtdn) = self.pages[page]
        self.panes.rawShow(txtup, txtdn)



FUZZYHELP = """\
<b>This is the syntax you can follow to generate 
multiple crafted requests.</b>

Every text inside two dollar signs (<i>$</i>) is a text 
generator (if you want to actually write a dollar sign, 
use $$). The system will generate and send as many requests
as the generator produces. 

If in a text you put more than one generator, the results
are combined. For example, if you put a generator of 5
digits and a generator of 10 letters, a total of 50 pages
will be generated. You can actually check how many
pages will be generated using the <i>Analyze</i> button 
(to actually see those requests, still without sending them, 
select the <i>preview</i> option).

Each generator between the dollar signs will be evaluated 
by Python, using <tt>eval()</tt>, with an almost clean 
namespace (there's already imported the module <tt>string</tt>).

For example, you can do:
<tt>
  Numbers from 0 to 4: $range(5)$
  First ten letters: $string.lowercase[:10]$
  The words "spam" and "eggs": $['spam', 'eggs']$
  The content of a file: 
      $[l.strip() for l in file('input.txt').readlines()]$
</tt>
"""


class FuzzyRequests(entries.RememberingWindow):
    '''Infrastructure to generate fuzzy HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, initialRequest=None):
        super(FuzzyRequests,self).__init__(w3af, "fuzzyreq", "w3af - Fuzzy Requests")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af
        mainhbox = gtk.HBox()
        
        # To store the responses
        self.responses = []
        
        # ---- left pane ----
        vbox = gtk.VBox()
        mainhbox.pack_start(vbox, False, False, padding=10)

        # we create the buttons first, to pass them
        analyzBut = gtk.Button("Analyze")
        sendBut = gtk.Button("Send all")
        
        # Fix content length checkbox
        self._fixContentLengthCB = gtk.CheckButton('Fix content length header')
        self._fixContentLengthCB.set_active(True)
        self._fixContentLengthCB.show()

        # request
        self.originalReq = reqResViewer.requestPaned(w3af, [analyzBut, sendBut],
                                        editable=True, widgname="fuzzyrequest")
        if initialRequest is None:
            self.originalReq.rawShow(request_example, '')
        else:
            (initialUp, initialDn) = initialRequest
            self.originalReq.rawShow(initialUp, initialDn)

        # help
        helplabel = gtk.Label()
        helplabel.set_markup(FUZZYHELP)
        self.originalReq.notebook.append_page(helplabel, gtk.Label("Syntax help"))
        helplabel.show()
        self.originalReq.notebook.show()
        vbox.pack_start(self.originalReq.notebook, True, True, padding=5)
        vbox.show()
        
        # the commands
        t = gtk.Table(2, 3)
        analyzBut.connect("clicked", self._analyze)
        t.attach(analyzBut, 0, 1, 0, 1)
        self.analyzefb = gtk.Label("0 requests")
        self.analyzefb.set_sensitive(False)
        t.attach(self.analyzefb, 1, 2, 0, 1)
        self.preview = gtk.CheckButton("Preview")
        t.attach(self.preview, 2, 3, 0, 1)
        sendBut.connect("clicked", self._send)
        t.attach(sendBut, 0, 1, 1, 2)
        self.sendfb = gtk.Label("0 ok, 0 errors")
        self.sendfb.set_sensitive(False)
        t.attach(self.sendfb, 1, 2, 1, 2)
        t.attach(self._fixContentLengthCB, 2, 3, 1, 2)
        t.show_all()
        
        vbox.pack_start(t, False, False, padding=5)
        
        
        # ---- right pane ----
        vbox = gtk.VBox()
        mainhbox.pack_start(vbox, padding=10)

        # result itself
        self.resultReqResp = reqResViewer.reqResViewer(w3af, withFuzzy=False, editableRequest=False, editableResponse=False)
        self.resultReqResp.set_sensitive(False)
        vbox.pack_start(self.resultReqResp, True, True, padding=5)
        vbox.show()
        
        # result control
        centerbox = gtk.HBox()
        self.pagesControl = entries.PagesControl(w3af, self._pageChange)
        centerbox.pack_start(self.pagesControl, True, False)
        centerbox.show()
        
        # cluster responses button
        image = gtk.Image()
        image.set_from_file( os.path.join( os.path.split(__file__)[0] ,'data','cluster_data.png'))
        image.show()
        self.clusterButton = gtk.Button(label='Cluster Responses')
        self.clusterButton.connect("clicked", self._clusterData )
        self.clusterButton.set_sensitive( False )
        self.clusterButton.set_image(image)
        self.clusterButton.show()
        centerbox.pack_start(self.clusterButton, True, False)
        
        # clear responses button
        self.clearButton = entries.SemiStockButton('Clear Responses', gtk.STOCK_CLEAR, \
                                                                    tooltip='Clear all HTTP responses from fuzzer window')
        self.clearButton.connect("clicked", self._clearResponses )
        self.clearButton.set_sensitive( False )
        self.clearButton.show()
        centerbox.pack_start(self.clearButton, True, False)
        
        vbox.pack_start(centerbox, False, False, padding=5)

        # Show all!
        self.vbox.pack_start(mainhbox)
        self.vbox.show()
        mainhbox.show()
        self.show()

    def _clearResponses( self, widg ):
        '''
        Clears all the responses from the fuzzy window.
        '''
        self.responses = []
        self.resultReqResp.request.clearPanes()
        self.resultReqResp.response.clearPanes()
        self.resultReqResp.set_sensitive(False)
        self.clusterButton.set_sensitive(False)
        self.clearButton.set_sensitive(False)
        self.pagesControl.deactivate()
        
    def _clusterData( self, widg):
        '''
        Analyze if we can cluster the responses and do it.
        '''
        data = [r[2] for r in self.responses if r[2] is not None]
        
        if data:
            window = clusterGraphWidget(self.w3af, data)
            window.connect('destroy', gtk.main_quit)
            gtk.main()
        else:
            # Let the user know ahout the problem
            msg = "There are no HTTP responses available to cluster."
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            opt = dlg.run()
            dlg.destroy()

    def _analyze(self, widg):
        '''Handles the Analyze part.'''
        (request, postbody) = self.originalReq.getBothTexts()
        try:
            fg = helpers.coreWrap(fuzzygen.FuzzyGenerator, request, postbody)
        except fuzzygen.FuzzyError:
            return
            
        # 
        preview = list(fg.generate())
        self.analyzefb.set_text("%d requests" % len(preview))
        self.analyzefb.set_sensitive(True)

        # raise the window only if preview is active
        if self.preview.get_active():
            PreviewWindow(self.w3af, self, preview)


    def _send(self, widg):
        '''Sends the requests.'''
        (request, postbody) = self.originalReq.getBothTexts()
        try:
            fg = helpers.coreWrap(fuzzygen.FuzzyGenerator, request, postbody)
        except fuzzygen.FuzzyError:
            return
            
        # let's send the requests!
        result_ok = 0
        result_err = 0
        allrequests = list(fg.generate())
        if len(allrequests) > 20:
            msg = "Are you sure you want to send %d requests?" % len(allrequests)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
            opt = dlg.run()
            dlg.destroy()
            if opt != gtk.RESPONSE_YES:
                return

        self.sendfb.set_sensitive(True)
        busy = gtk.gdk.Window(self.window, gtk.gdk.screen_width(), gtk.gdk.screen_height(), gtk.gdk.WINDOW_CHILD, 0, gtk.gdk.INPUT_ONLY)
        busy.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        busy.show()
        while gtk.events_pending():
            gtk.main_iteration()
        
        # Get the fix content length value
        fixContentLength = self._fixContentLengthCB.get_active()
        
        for (realreq, realbody) in allrequests:
            try:
                httpResp = self.w3af.uriOpener.sendRawRequest(realreq, realbody, fixContentLength)
                errorMsg = None
                result_ok += 1
            except w3afException, e:
                errorMsg = str(e)
                httpResp = None
                result_err += 1
            except w3afMustStopException, e:
                errorMsg = str(e)
                httpResp = None
                result_err += 1

                # Let the user know ahout the problem
                msg = "Stopped sending requests because " + str(e)
                dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
                opt = dlg.run()
                dlg.destroy()
                break
            self.responses.append((realreq, realbody, httpResp, errorMsg))
            
            # Always update the gtk stuff
            self.sendfb.set_text("%d ok, %d errors" % (result_ok, result_err))
            while gtk.events_pending():
                gtk.main_iteration()

        # activate and show
        busy.destroy()
        self.resultReqResp.set_sensitive(True)
        self.clearButton.set_sensitive(True)
        if len(self.responses) >=3:
            self.clusterButton.set_sensitive(True)
        self.pagesControl.activate(len(self.responses))
        self._pageChange(0)

    def _pageChange(self, page):
        (realreq, realbody, responseObj, errorMsg) = self.responses[page]

        self.resultReqResp.request.rawShow(realreq, realbody)
        if responseObj is not None:
            self.resultReqResp.response.showObject(responseObj)
        else:
            self.resultReqResp.response.showError(errorMsg)
