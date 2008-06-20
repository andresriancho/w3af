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

import pygtk, gtk, gobject
from . import reqResViewer, helpers, entries, fuzzygen
from .clusterView import clusterCellWindow
from core.controllers.w3afException import *
import os

request_example = """\
GET http://localhost/path HTTP/1.0
Host: www.some_host.com
User-Agent: w3af.sf.net
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
"""

class ManualRequests(entries.RememberingWindow):
    '''Infrastructure to generate manual HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, initialRequest=None):
        super(ManualRequests,self).__init__(w3af, "manualreq", "w3af - Manual Requests")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
        self.w3af = w3af

        # send button
        hbox = gtk.HBox()
        b = gtk.Button("   Send   ")
        b.connect("clicked", self._send)
        hbox.pack_start(b, True, False)

        # request-response viewer
        self.reqresp = reqResViewer.reqResViewer(w3af, [b], withManual=False, editableRequest=True)
        self.reqresp.response.set_sensitive(False)
        self.vbox.pack_start(self.reqresp, True, True)

        self.vbox.pack_start(hbox, False, False)
        
        # Add a default request
        if initialRequest is None:
            self.reqresp.request.rawShow(request_example, '')
        else:
            (initialUp, initialDn) = initialRequest
            self.reqresp.request.rawShow(initialUp, initialDn)
        
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
            self.reqresp.response.set_sensitive(False)
            return
        except w3afMustStopException, mse:
            self.reqresp.response.clearPanes()
            self.reqresp.response.set_sensitive(False)
            # Let the user know ahout the problem, this was a serious one.
            msg = "Stopped sending requests because " + str(mse)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            opt = dlg.run()
            dlg.destroy()
            return

        # activate and show
        self.reqresp.response.set_sensitive(True)
        self.reqresp.response.showObject(httpResp)


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
        self.panes = reqResViewer.requestPaned(editable=False)
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
(to actually see those requests, still without sending them, select
the <i>preview</i> option).

Each generator between the dollar signs will be evaluated 
by Python, using <tt>eval()</tt>, with an almost clean 
namespace (there's already imported the module <tt>string</tt>).

For example, you can do:
<tt>
    Numbers from 0 to 4: $range(5)$
    First ten letters: $string.lowercase[:10]$
    The words "spam" and "eggs": $['spam', 'eggs']$
    The content of a file: $[l.strip() for l in file('input.txt').readlines()]$
</tt>
"""

class FuzzyRequests(entries.RememberingWindow):
    '''Infrastructure to generate fuzzy HTTP requests.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, initialRequest=None):
        super(FuzzyRequests,self).__init__(w3af, "fuzzyreq", "w3af - Fuzzy Requests")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
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

        # request
        self.originalReq = reqResViewer.requestPaned([analyzBut, sendBut], editable=True)
        if initialRequest is None:
            self.originalReq.rawShow(request_example, '')
        else:
            (initialUp, initialDn) = initialRequest
            self.originalReq.rawShow(initialUp, initialDn)

        # help
        helplabel = gtk.Label()
        helplabel.set_markup(FUZZYHELP)
        self.originalReq.notebook.append_page(helplabel, gtk.Label("Syntax help"))
        vbox.pack_start(self.originalReq.notebook, True, True, padding=5)

        # the commands
        t = gtk.Table(2, 3)
        analyzBut.connect("clicked", self._analyze)
        t.attach(analyzBut, 0, 1, 0, 1)
        self.analyzefb = gtk.Label("0 requests")
        self.analyzefb.set_sensitive(False)
        t.attach(self.analyzefb, 1, 2, 0, 1)
        self.preview = gtk.CheckButton("preview")
        t.attach(self.preview, 2, 3, 0, 1)
        sendBut.connect("clicked", self._send)
        t.attach(sendBut, 0, 1, 1, 2)
        self.sendfb = gtk.Label("0 ok, 0 errors")
        self.sendfb.set_sensitive(False)
        t.attach(self.sendfb, 1, 2, 1, 2)
        vbox.pack_start(t, False, False, padding=5)

        # ---- right pane ----
        vbox = gtk.VBox()
        mainhbox.pack_start(vbox, padding=10)

        # result itself
        self.resultReqResp = reqResViewer.reqResViewer(w3af, withFuzzy=False, editableRequest=False, editableResponse=False)
        self.resultReqResp.set_sensitive(False)
        vbox.pack_start(self.resultReqResp, True, True, padding=5)

        # result control
        centerbox = gtk.HBox()
        self.pagesControl = entries.PagesControl(w3af, self._pageChange)
        centerbox.pack_start(self.pagesControl, True, False)
        
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
        centerbox.pack_start(self.clearButton, True, False)
        
        vbox.pack_start(centerbox, False, False, padding=5)

        # Show all!
        self.vbox.pack_start(mainhbox)
        self.show_all()

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
            clusterCellWindow( self.w3af, data=data )
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
        for (realreq, realbody) in allrequests:
            try:
                httpResp = self.w3af.uriOpener.sendRawRequest(realreq, realbody)
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




ui_proxy_menu = """
<ui>
  <toolbar name="Toolbar">
    <toolitem action="Active"/>
    <toolitem action="TrapReq"/>
    <separator name="sep1"/>
    <toolitem action="Config"/>
    <separator name="sep2"/>
    <toolitem action="Help"/>
  </toolbar>
</ui>
"""

class ProxiedRequests(entries.RememberingWindow):
    '''Proxies the HTTP requests, allowing modifications.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(ProxiedRequests,self).__init__(w3af, "proxytool", "w3af - Proxy", onDestroy=self._close)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
        self.w3af = w3af

        # toolbar elements
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')
        actiongroup.add_actions([
            ('Help', gtk.STOCK_HELP, '_Help', None, 'Help regarding this window', self._help),
            ('Config', gtk.STOCK_EDIT, '_Configuration', None, 'Configure the proxy', self._config),
        ])
        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('Active', gtk.STOCK_EXECUTE,  '_Activate', None, 'Activate/Deactivate the Proxy', self._toggle_active, True),
            ('TrapReq', gtk.STOCK_JUMP_TO, '_Trap Requests',    None, 'Trap the requests or not',    self._toggle_trap, True),
        ])

        # finish the toolbar
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(ui_proxy_menu)
        toolbar = uimanager.get_widget('/Toolbar')
        assert toolbar.get_n_items() == 6
        separat = toolbar.get_nth_item(4)
        separat.set_draw(False)
        separat.set_expand(True)
        self.vbox.pack_start(toolbar, False)

        # the buttons
        hbox = gtk.HBox()
        self.bt_drop = gtk.Button("  Drop  ")
        self.bt_drop.connect("clicked", self._drop)
        hbox.pack_start(self.bt_drop, True, False)
        self.bt_send = gtk.Button("  Send  ")
        self.bt_send.connect("clicked", self._send)
        hbox.pack_start(self.bt_send, True, False)
        self.bt_next = gtk.Button("  Next  ")
        self.bt_next.set_sensitive(False)
        self.bt_next.connect("clicked", self._next)
        hbox.pack_start(self.bt_next, True, False)

        # request-response viewer
        self.reqresp = reqResViewer.reqResViewer(w3af, [self.bt_drop, self.bt_send], editableRequest=True)
        self.reqresp.request.set_sensitive(False)
        self.reqresp.response.set_sensitive(False)
        self.vbox.pack_start(self.reqresp, True, True)

        self.vbox.pack_start(hbox, False, False)
        
        # finish it
        self.waitingRequests = True
        self.keepChecking = True
        gobject.timeout_add(500, self._superviseRequests)
        self.show_all()

    def _superviseRequests(self, *a):
        '''Supervise if there're requests to show.

        @return: True to gobject to keep calling it, False when all is done.
        '''
        if not self.waitingRequests:
            return self.keepChecking

        # check if there's something queued

        # if there's something, set it up

        # if not, grey it out

        return self.keepChecking

    def _drop(self, widg=None):
        '''Discards the actual request.

        @param widget: who sent the signal.
        '''
        print "FIXME: drop"
        # drop the request

        self.waitingRequests = True

    def _send(self, widg):
        '''Sends the request through the proxy.

        @param widget: who sent the signal.
        '''
        print "FIXME: drop"
        # send the request and show the response
        self.bt_next.set_sensitive(True)

    def _next(self, widg):
        '''Moves to the next request.

        @param widget: who sent the signal.
        '''
        print "FIXME: drop"
        # clean the response
        self._drop()

    def _close(self):
        '''Closes everything.'''
        self.keepChecking = False
        return True

    def _toggle_active(self, action):
        '''Start/stops the proxy.'''
        print "FIXME: toggle active"

    def _toggle_trap(self, action):
        '''Toggle the trap flag.'''
        print "FIXME: toggle trap"

    def _config(self, action):
        '''Open the configuration dialog.'''
        print "FIXME: configuration"

    def _help(self, action):
        '''Shows the help.'''
        print "FIXME: implement the help!"
