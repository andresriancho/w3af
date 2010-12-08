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

import gtk
import gobject
import threading
import functools
import os

from . import reqResViewer, helpers, entries, fuzzygen
# Alternative ways of seeing the data
from .clusterGraph import distance_function_selector
# Generators
from .payload_generators import create_generator_menu
from core.data.db.history import HistoryItem
from core.controllers.w3afException import w3afException, w3afMustStopException

ui_proxy_menu = """
<ui>
  <toolbar name="Toolbar">
    <toolitem action="Send"/>
    <separator name="sep1"/>
  </toolbar>
</ui>
"""
manual_request_example = """\
GET http://localhost/script.php HTTP/1.0
Host: www.some_host.com
User-Agent: w3af.sf.net
Pragma: no-cache
Content-Type: application/x-www-form-urlencoded
"""

fuzzy_request_example = """\
GET http://localhost/$xrange(10)$ HTTP/1.0
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
            self.httpResp = self.w3af.uriOpener.sendRawRequest(self.tsup,\
                    self.tlow, self.fixContentLength)
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
        super(ManualRequests,self).__init__(
            w3af, "manualreq", "w3af - Manual Requests", "Manual_Requests")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af
        self._uimanager = gtk.UIManager()
        accelgroup = self._uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')
        actiongroup.add_actions([
            ('Send', gtk.STOCK_YES, _('_Send Request'), None, _('Send request'), self._send),
        ])
        # Finish the toolbar
        self._uimanager.insert_action_group(actiongroup, 0)
        self._uimanager.add_ui_from_string(ui_proxy_menu)
        toolbar = self._uimanager.get_widget('/Toolbar')
        b = toolbar.get_nth_item(0)
        self.vbox.pack_start(toolbar, False)
        toolbar.show()
        # Fix content length checkbox
        self._fixContentLengthCB = gtk.CheckButton('Fix content length header')
        self._fixContentLengthCB.set_active(True)
        self._fixContentLengthCB.show()
        # request-response viewer
        self.reqresp = reqResViewer.reqResViewer(w3af, [b.set_sensitive],\
                withManual=False, editableRequest=True)
        self.reqresp.response.set_sensitive(False)
        self.vbox.pack_start(self._fixContentLengthCB, False, False)
        self.vbox.pack_start(self.reqresp, True, True)
        # Add a default request
        if initialRequest is None:
            self.reqresp.request.showRaw(manual_request_example, '')
        else:
            (initialUp, initialDn) = initialRequest
            self.reqresp.request.showRaw(initialUp, initialDn)

        # Show all!
        self.show()

    def _send(self, widg):
        '''Actually generates the manual requests.

        @param widget: who sent the signal.
        '''
        (tsup, tlow) = self.reqresp.request.getBothTexts()

        busy = gtk.gdk.Window(self.window, gtk.gdk.screen_width(),\
                gtk.gdk.screen_height(), gtk.gdk.WINDOW_CHILD,\
                0, gtk.gdk.INPUT_ONLY)
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
                self.reqresp.nb.next_page()
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
    def __init__(self, w3af, parent, fg):
        super(PreviewWindow,self).__init__(
            w3af, "fuzzypreview", "Preview", "Fuzzy_Requests")
        self.pages = []
        self.generator = fg.generate()
        self.set_modal(True)
        self.set_transient_for(parent)

        # content
        self.panes = reqResViewer.requestPart(w3af, editable=False, widgname="fuzzypreview")
        self.vbox.pack_start(self.panes)
        self.panes.show()


        # the ok button
        centerbox = gtk.HBox()
        quant = fg.calculateQuantity()
        self.pagesControl = entries.PagesControl(w3af, self._pageChange, quant)
        centerbox.pack_start(self.pagesControl, True, False)
        centerbox.show()
        self.vbox.pack_start(centerbox, False, False, padding=5)

        self._pageChange(0)

        self.vbox.show()
        self.show()

    def _pageChange(self, page):
        while len(self.pages) <= page:
            it = self.generator.next()
            self.pages.append(it)
        (txtup, txtdn) = self.pages[page]
        self.panes.showRaw(txtup, txtdn)



FUZZYHELP = """\
<b>This is the syntax you can follow to generate
multiple crafted requests.</b>

Every text inside two dollar signs (<i>$</i>) is a text
generator (if you want to actually write a dollar sign,
use \$). The system will generate and send as many requests
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
Keep in mind that copying some random text into the request window
is almost as dangerous as pasting some random text into a console
window: you could be executing OS commands in your box.

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
        super(FuzzyRequests,self).__init__(
            w3af, "fuzzyreq", "w3af - Fuzzy Requests", "Fuzzy_Requests")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af
        self.historyItem = HistoryItem()
        mainhbox = gtk.HBox()

        # To store the responses
        self.responses = []

        # ---- left pane ----
        vbox = gtk.VBox()
        mainhbox.pack_start(vbox, False, False)

        # we create the buttons first, to pass them
        analyzBut = gtk.Button("Analyze")
        self.sendPlayBut = entries.SemiStockButton("", gtk.STOCK_MEDIA_PLAY, "Sends the pending requests")
        self.sendStopBut = entries.SemiStockButton("", gtk.STOCK_MEDIA_STOP, "Stops the request being sent")
        self.sSB_state = helpers.PropagateBuffer(self.sendStopBut.set_sensitive)
        self.sSB_state.change(self, False)

        # Fix content length checkbox
        self._fixContentLengthCB = gtk.CheckButton('Fix content length header')
        self._fixContentLengthCB.set_active(True)
        self._fixContentLengthCB.show()

        # request
        self.originalReq = reqResViewer.requestPart(w3af,\
                [analyzBut.set_sensitive, self.sendPlayBut.set_sensitive,\
                functools.partial(self.sSB_state.change, "rRV")],\
                editable=True, widgname="fuzzyrequest")

        if initialRequest is None:
            self.originalReq.showRaw(fuzzy_request_example, '')
        else:
            (initialUp, initialDn) = initialRequest
            self.originalReq.showRaw(initialUp, initialDn)

        # Add the right button popup menu to the text widgets
        rawTextView = self.originalReq.getViewById('HttpRawView')
        rawTextView.textView.connect("populate-popup", self._populate_popup)

        # help
        helplabel = gtk.Label()
        helplabel.set_selectable(True)
        helplabel.set_markup(FUZZYHELP)
        self.originalReq.append_page(helplabel, gtk.Label("Syntax help"))
        helplabel.show()
        self.originalReq.show()
        vbox.pack_start(self.originalReq, True, True, padding=5)
        vbox.show()

        # the commands
        t = gtk.Table(2, 4)
        analyzBut.connect("clicked", self._analyze)
        t.attach(analyzBut, 0, 2, 0, 1)
        self.analyzefb = gtk.Label("0 requests")
        self.analyzefb.set_sensitive(False)
        t.attach(self.analyzefb, 2, 3, 0, 1)
        self.preview = gtk.CheckButton("Preview")
        t.attach(self.preview, 3, 4, 0, 1)
        self.sPB_signal = self.sendPlayBut.connect("clicked", self._send_start)
        t.attach(self.sendPlayBut, 0, 1, 1, 2)
        self.sendStopBut.connect("clicked", self._send_stop)
        t.attach(self.sendStopBut, 1, 2, 1, 2)
        self.sendfb = gtk.Label("0 ok, 0 errors")
        self.sendfb.set_sensitive(False)
        t.attach(self.sendfb, 2, 3, 1, 2)
        t.attach(self._fixContentLengthCB, 3, 4, 1, 2)
        t.show_all()

        vbox.pack_start(t, False, False, padding=5)

        # ---- throbber pane ----
        vbox = gtk.VBox()
        self.throbber = helpers.Throbber()
        self.throbber.set_sensitive(False)
        vbox.pack_start(self.throbber, False, False)
        vbox.show()
        mainhbox.pack_start(vbox, False, False)

        # ---- right pane ----
        vbox = gtk.VBox()
        mainhbox.pack_start(vbox)

        # A label to show the id of the response
        self.title0 = gtk.Label()
        self.title0.show()
        vbox.pack_start(self.title0, False, True)

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
        self._sendPaused = True
        self.vbox.pack_start(mainhbox)
        self.vbox.show()
        mainhbox.show()
        self.show()

    def _populate_popup(self, textview, menu):
        '''Populates the menu with the fuzzing items.'''
        menu.append(gtk.SeparatorMenuItem())
        main_generator_menu = gtk.MenuItem(_("Generators"))
        main_generator_menu.set_submenu(create_generator_menu(self))
        menu.append(main_generator_menu)
        menu.show_all()

    def _clearResponses( self, widg ):
        '''Clears all the responses from the fuzzy window.'''
        self.responses = []
        self.resultReqResp.request.clearPanes()
        self.resultReqResp.response.clearPanes()
        self.resultReqResp.set_sensitive(False)
        self.clusterButton.set_sensitive(False)
        self.clearButton.set_sensitive(False)
        self.pagesControl.deactivate()

    def _clusterData( self, widg):
        '''Analyze if we can cluster the responses and do it.'''
        data = []
        for resp in self.responses:
            if resp[0]:
                reqid = resp[1]
                historyItem = self.historyItem.read(reqid)
                data.append(historyItem.response)

        if data:
            distance_function_selector(self.w3af, data)
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

        self.analyzefb.set_text("%d requests" % fg.calculateQuantity())
        self.analyzefb.set_sensitive(True)

        # raise the window only if preview is active
        if self.preview.get_active():
            PreviewWindow(self.w3af, self, fg)

    def _send_stop(self, widg=None):
        '''Stop the requests being sent.'''
        self._sendStopped = True
        self.sendPlayBut.changeInternals("", gtk.STOCK_MEDIA_PLAY, "Sends the pending requests")
        self.sendPlayBut.disconnect(self.sPB_signal)
        self.sPB_signal = self.sendPlayBut.connect("clicked", self._send_start)
        self.sSB_state.change(self, False)
        self.throbber.running(False)

    def _send_pause(self, widg):
        '''Pause the requests being sent.'''
        self._sendPaused = True
        self.sendPlayBut.changeInternals("", gtk.STOCK_MEDIA_PLAY, "Sends the pending requests")
        self.sendPlayBut.disconnect(self.sPB_signal)
        self.sPB_signal = self.sendPlayBut.connect("clicked", self._send_play)
        self.throbber.running(False)

    def _send_play(self, widg):
        '''Continue sending the requests.'''
        self._sendPaused = False
        self.sendPlayBut.changeInternals("", gtk.STOCK_MEDIA_PAUSE, "Sends the pending requests")
        self.sendPlayBut.disconnect(self.sPB_signal)
        self.sPB_signal = self.sendPlayBut.connect("clicked", self._send_pause)
        self.throbber.running(True)

    def _send_start(self, widg):
        '''Start sending the requests.'''
        (request, postbody) = self.originalReq.getBothTexts()
        try:
            fg = helpers.coreWrap(fuzzygen.FuzzyGenerator, request, postbody)
        except fuzzygen.FuzzyError:
            return

        quant = fg.calculateQuantity()
        if quant > 20:
            msg = "Are you sure you want to send %d requests?" % quant
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
            opt = dlg.run()
            dlg.destroy()
            if opt != gtk.RESPONSE_YES:
                return

        # Get the fix content length value
        fixContentLength = self._fixContentLengthCB.get_active()

        # initial state
        self.result_ok = 0
        self.result_err = 0
        self._sendPaused = False
        self._sendStopped = False
        requestGenerator = fg.generate()

        # change the buttons
        self.sendPlayBut.changeInternals("", gtk.STOCK_MEDIA_PAUSE, "Pauses the requests sending")
        self.sendPlayBut.disconnect(self.sPB_signal)
        self.sPB_signal = self.sendPlayBut.connect("clicked", self._send_pause)
        self.sSB_state.change(self, True)
        self.throbber.running(True)

        # let's send the requests!
        gobject.timeout_add(100, self._real_send, fixContentLength, requestGenerator)


    def _real_send(self, fixContentLength, requestGenerator):
        '''This is the one that actually sends the requests, if corresponds.

        @param fixContentLength: if the lenght should be fixed by the core.
        @param requestGenerator: where to ask for the requests
        '''
        if self._sendStopped:
            return False
        if self._sendPaused:
            return True

        try:
            (realreq, realbody) = requestGenerator.next()
        except StopIteration:
            # finished with all the requests!
            self._send_stop()
            return False

        try:
            httpResp = self.w3af.uriOpener.sendRawRequest(realreq, realbody, fixContentLength)
            errorMsg = None
            self.result_ok += 1
        except w3afException, e:
            errorMsg = str(e)
            httpResp = None
            self.result_err += 1
        except w3afMustStopException, e:
            errorMsg = str(e)
            httpResp = None
            self.result_err += 1

            # Let the user know ahout the problem
            msg = "Stopped sending requests because " + str(e)
            helpers.friendlyException( msg )
            return False

        if httpResp is not None:
            self.responses.append((True, httpResp.getId()))
        else:
            self.responses.append((False, realreq, realbody, errorMsg))

        # always update the gtk stuff
        self.sendfb.set_sensitive(True)
        self.sendfb.set_text("%d ok, %d errors" % (self.result_ok, self.result_err))

        # activate and show
        self.resultReqResp.set_sensitive(True)
        self.clearButton.set_sensitive(True)
        if len(self.responses) >=3:
            self.clusterButton.set_sensitive(True)
        self.pagesControl.activate(len(self.responses))
        self._pageChange(0)
        return True

    def _pageChange(self, page):
        '''
        Change the page, and show the information that was stored in self.responses
            
        If OK, the responses are saved like this:
            self.responses.append((True, httpResp.getId()))
        
        else:
            self.responses.append((False, realreq, realbody, errorMsg))        
        
        @return: None.
        '''
        info = self.responses[page]
        if info[0]:
            reqid = info[1]
            # no need to verify if it was ok: the request was succesful and
            # surely existant
            try:
                historyItem = self.historyItem.read(reqid)
            except IndexError:
                #
                # This catches a strange error 
                # https://sourceforge.net/tracker/?func=detail&aid=2696941&group_id=170274&atid=853652
                # TODO: Investigate this further...
                #
                error_msg = 'Error searching the request database'
                self.resultReqResp.request.showRaw( error_msg, error_msg )
                self.resultReqResp.response.showError( error_msg )
                self.title0.set_markup( "<b>Error</b>")
            else:
                self.resultReqResp.request.showObject( historyItem.request )
                self.resultReqResp.response.showObject( historyItem.response )
                self.title0.set_markup( "<b>Id: %d</b>" % reqid )
        else:
            # the request brought problems
            realreq, realbody, errorMsg = info[1:]
            self.resultReqResp.request.showRaw( realreq, realbody )
            self.resultReqResp.response.showError( errorMsg )
            self.title0.set_markup( "<b>Error</b>")
