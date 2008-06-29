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
from core.data.options.option import option as Option
from core.controllers.daemons import localproxy
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

class ProxyOptions(object):
    def __init__(self):
        self.options = []

    def append(self, name, option):
        self.options.append(option)
        setattr(self, name, option)

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

        # notebook
        nb = gtk.Notebook()
        nb.append_page(self.reqresp, gtk.Label("Request and Response"))
        lab1 = gtk.Label("Coming soon! :)")
        lab1.set_sensitive(False)
        lab2 = gtk.Label("History")
        lab2.set_sensitive(False)
        nb.append_page(lab1, lab2)
        self.vbox.pack_start(nb, True, True)

        self.vbox.pack_start(hbox, False, False)
        
        # the config options
        self.proxyoptions = ProxyOptions()
        self.proxyoptions.append("ignoreimgs", 
                Option("Ignore images", False, "Ignore images", "boolean", "Ignore images by extension"))
        self.proxyoptions.append("ipport", 
                Option("Where to listen", "localhost:8080", "IP:port", "ipport", "IP and port where to listen"))
        self.proxyoptions.append("trap", 
                Option("What to trap", ".*", "URLs to trap", "string", "REGEX that indicates what URL to trap"))

        # finish it
        self._startProxy()
        self.waitingRequests = True
        self.keepChecking = True
        gobject.timeout_add(500, self._superviseRequests)
        self.show_all()

    def _startProxy(self):
        '''Starts the proxy.'''
        ipport = self.proxyoptions.ipport.getValue() 
        ip, port = ipport.split(":")
        self.w3af.mainwin.sb("Starting local proxy")
        self.proxy = localproxy.localproxy(ip, int(port))
        self.proxy.start2()

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
#Drop: Only enabled if we have a request that hasn't been sent to the
#server yet. When the user clicks on drop the request textview is
#cleared (the response view has nothing in it at this moment, so no
#need to clear it) and the user interface just forgets about this
#request.

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
        print "FIXME: next"
#        Next: Only enabled after sending a request, and while viewing a
#response. Clears the textviews that show the request and the response.
#The request and response is going to be saved by the core in order to
#be viewed by the history notebook.


    def _close(self):
        '''Closes everything.'''
        self.keepChecking = False
        # FIXME: poner aca una pregunta "seguro salir y cerrar el proxy?"
        self.proxy.stop()
        return True

    def _toggle_active(self, widget):
        '''Start/stops the proxy.'''
        proxyactive = widget.get_active()
        if proxyactive:
            self._startProxy()
        else:
            self.w3af.mainwin.sb("Stopping local proxy")
            self.proxy.stop()

    def _toggle_trap(self, widget):
        '''Toggle the trap flag.'''
        trapactive = widget.get_active()
        self.proxy.setTrap(trapactive)

    def _config(self, action):
        '''Open the configuration dialog.'''
        previous_ipport = self.proxyoptions.ipport.getValue()
        ConfigDialog("Configuration", self.w3af, self.proxyoptions.options)

        # shutdown/restart if needed
        new_ipport = self.proxyoptions.ipport.getValue() 
        if new_ipport != previous_ipport:
            self.w3af.mainwin.sb("Stopping local proxy")
            self.proxy.stop()
            self._startProxy()

        # rest of config
        self.proxy.setWhatToTrap(self.proxyoptions.trap.getValue())
        self.proxy.setIgnoreImages(self.proxyoptions.ignoreimgs.getValue())

    def _help(self, action):
        '''Shows the help.'''
        print "FIXME: implement the help!"


class ConfigOptions(gtk.VBox):
    '''Only the options for configuration.

    @param w3af: The Core
    @param confdialog: The parent widget
    @param options: The options to configure.
    @param save_btn: The save button.
    @param rvrt_btn: The revert button.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, confdialog, options, save_btn, rvrt_btn):
        super(ConfigOptions,self).__init__()
        self.set_spacing(5)
        self.w3af = w3af
        self.confdialog = confdialog
        self.widgets_status = {}
        self.tab_widget = {}
        self.propagAnyWidgetChanged = helpers.PropagateBuffer(self._changedAnyWidget)
        self.propagLabels = {}

        # options
        self.options = options

        # buttons
        save_btn.connect("clicked", self._savePanel)
        save_btn.set_sensitive(False)
        rvrt_btn.set_sensitive(False)
        rvrt_btn.connect("clicked", self._revertPanel)
        self.save_btn = save_btn
        self.rvrt_btn = rvrt_btn
        
        # middle (the heart of the panel)
        if self.options:
            tabbox = gtk.HBox()
            heart = self._createNotebook()
            tabbox.pack_start(heart, expand=True)
            tabbox.show()
            self.pack_start(tabbox, expand=True, fill=False)
        self.show()

    def _createNotebook(self):
        '''This create the notebook with all the options.

        @return: The created notebook if more than one grouping
        '''
        # let's get the tabs, but in order!
        tabs = []
        for o in self.options:
            t = o.getTabId()
            if t not in tabs:
                tabs.append(t)

        # see if we have more than a tab to create a nb
        if len(tabs) < 2:
            table = self._makeTable(self.options, None)
            return table

        # the notebook
        nb = gtk.Notebook()
        for tab in tabs:
            options = [x for x in self.options if x.getTabId() == tab]
            if not tab:
                tab = "General"
            label = gtk.Label(tab)
            prop = helpers.PropagateBufferPayload(self._changedLabelNotebook, label, tab)
            table = self._makeTable(options, prop)
            nb.append_page(table, label)
        nb.show()
        return nb

    def _makeTable(self, options, prop):
        '''Creates the table in which the options are shown.

        @param options: The options to show
        @param prop: The propagation function for this options
        @return: The created table

        For each row, it will put:

            - the option label
            - the configurable widget (textentry, checkbox, etc.)
            - an optional button to get more help (if the help is available)

        Also, the configurable widget gets a tooltip for a small description.
        '''
        table = entries.EasyTable(len(options), 3)
        tooltips = gtk.Tooltips()
        for i,opt in enumerate(options):
            titl = gtk.Label(opt.getName())
            titl.set_alignment(0.0, 0.5)
            widg = entries.wrapperWidgets[opt.getType()](self._changedWidget, opt )            
            opt.widg = widg
            tooltips.set_tip(widg, opt.getDesc())
            if opt.getHelp():
                helpbtn = entries.SemiStockButton("", gtk.STOCK_INFO)
                cleanhelp = helpers.cleanDescription(opt.getHelp())
                helpbtn.connect("clicked", self._showHelp, cleanhelp)
            else:
                helpbtn = None
            table.autoAddRow(titl, widg, helpbtn)
            self.widgets_status[widg] = (titl, opt.getName(), "<b>%s</b>" % opt.getName())
            self.propagLabels[widg] = prop
        table.show()
        return table

    def _changedAnyWidget(self, like_initial):
        '''Adjust the save/revert buttons and alert the tree of the change.

        @param like_initial: if the widgets are modified or not.

        It only will be called if any widget changed its state, through
        a propagation buffer.
        '''
        self.save_btn.set_sensitive(not like_initial)
        self.rvrt_btn.set_sensitive(not like_initial)
        self.confdialog.like_initial = like_initial

    def _changedLabelNotebook(self, like_initial, label, text):
        if like_initial:
            label.set_text(text)
        else:
            label.set_markup("<b>%s</b>" % text)

    def _changedWidget(self, widg, like_initial):
        '''Receives signal when a widget changed or not.

        @param widg: the widget who changed.
        @param like_initial: if it's modified or not

        Handles the boldness of the option label and then propagates
        the change.
        '''
        (labl, orig, chng) = self.widgets_status[widg]
        if like_initial:
            labl.set_text(orig)
        else:
            labl.set_markup(chng)
        self.propagAnyWidgetChanged.change(widg, like_initial)
        propag = self.propagLabels[widg]
        if propag is not None:
            propag.change(widg, like_initial)

    def _showHelp(self, widg, helpmsg):
        '''Shows a dialog with the help message of the config option.

        @param widg: the widget who generated the signal
        @param helpmsg: the message to show in the dialog
        '''
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, helpmsg)
        dlg.set_title('Plugin help')
        dlg.run()
        dlg.destroy()

    def _savePanel(self, widg):
        '''Saves the config changes to the plugins.

        @param widg: the widget who generated the signal

        First it checks if there's some invalid configuration, then gets the value of 
        each option and save them to the plugin.
        '''
        # check if all widgets are valid
        invalid = []
        for opt in self.options:
            if hasattr(opt.widg, "isValid"):
                if not opt.widg.isValid():
                    invalid.append(opt.getName())
        if invalid:
            msg = "The configuration can't be saved, there is a problem in the following parameter(s):\n\n"
            msg += "\n-".join(invalid)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title('Configuration error')
            dlg.run()
            dlg.destroy()
            return

        # Get the value from the GTK widget and set it to the option object
        for opt in self.options:
            opt.setValue( opt.widg.getValue() )

        for opt in self.options:
            opt.widg.save()
        self.w3af.mainwin.sb("Configuration saved successfully")

    def _revertPanel(self, *vals):
        '''Revert all widgets to their initial state.'''
        for widg in self.widgets_status:
            widg.revertValue()
        self.w3af.mainwin.sb("The configuration was reverted to its last saved state")


class ConfigDialog(gtk.Dialog):
    '''Puts a Config panel inside a Dialog.
    
    @param title: the title of the window.
    @param w3af: the Core instance

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title, w3af, options):
        super(ConfigDialog,self).__init__(title, None, gtk.DIALOG_MODAL, ())
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')

        # buttons and config panel
        save_btn = self._button("Save configuration")
        rvrt_btn = self._button("Revert to previous configuration")
        close_btn = self._button(stock=gtk.STOCK_CLOSE)
        close_btn.connect("clicked", self._btn_close)
        self._panel = ConfigOptions(w3af, self, options, save_btn, rvrt_btn)
        self.vbox.pack_start(self._panel)

        self.like_initial = True
        self.connect("event", self._evt_close)
        self.run()
        self.destroy()

    def _button(self, text="", stock=None):
        b = gtk.Button(text, stock)
        b.show()
        self.action_area.pack_start(b)
        return b

    def configChanged(self, like_initial):
        '''Propagates the change from the options.

        @params like_initial: If the config is like the initial one
        '''
        print "changed!"
        self.like_initial = like_initial

    def _evt_close(self, widget, event):
        '''Handles the user trying to close the configuration.

        Filters by event.
        '''
        if event.type != gtk.gdk.DELETE:
            return False
        return self._close()

    def _btn_close(self, widget):
        '''Handles the user trying to close the configuration.'''
        if not self._close():
            self.emit("delete_event", gtk.gdk.Event(gtk.gdk.DELETE))

    def _close(self):
        '''Generic close.'''
        if self.like_initial:
            return False

        msg = "Do you want to quit without saving the changes?"
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
        stayhere = dlg.run() != gtk.RESPONSE_YES
        dlg.destroy()
        return stayhere

