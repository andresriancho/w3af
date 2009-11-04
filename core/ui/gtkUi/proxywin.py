"""
proxywin.py

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

"""

import gtk
import gobject
import os
import webbrowser

from . import reqResViewer, helpers, entries, httpLogTab
from core.controllers.w3afException import w3afException, w3afProxyException
from core.data.options.option import option as Option
from core.controllers.daemons import localproxy
import core.controllers.outputManager as om

ui_proxy_menu = """
<ui>
  <toolbar name="Toolbar">
    <toolitem action="Active"/>
    <toolitem action="TrapReq"/>
    <separator name="sep1"/>
    <toolitem action="Drop"/>
    <toolitem action="Send"/>
    <toolitem action="Next"/>
    <separator name="sep2"/>
    <toolitem action="Help"/>
  </toolbar>
</ui>
"""

class ProxyOptions(object):
    """Stores the proxy options."""
    def __init__(self):
        self.options = []

    def append(self, name, option):
        self.options.append(option)
        setattr(self, name, option)

class ProxiedRequests(entries.RememberingWindow):
    """Proxies the HTTP requests, allowing modifications.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af):
        '''Constructor.'''
        super(ProxiedRequests,self).__init__(
            w3af, "proxytool", _("w3af - Proxy"), "Using_the_Proxy",
            onDestroy=self._close)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.w3af = w3af
        self.def_padding = 5

        # Toolbar elements
        self._uimanager = gtk.UIManager()
        accelgroup = self._uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')
        actiongroup.add_actions([
            ('Help', gtk.STOCK_HELP, _('_Help'), None, _('Help regarding this window'), self._help),
            ('Drop', gtk.STOCK_CANCEL, _('_Drop Request'), None, _('Drop request'), self._drop),
            ('Send', gtk.STOCK_YES, _('_Send Request'), None, _('Send request'), self._send),
            ('Next', gtk.STOCK_GO_FORWARD, _('_Next Request'), None, _('Move to the next request'), self._next),
        ])
        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('Active', gtk.STOCK_EXECUTE,  _('_Activate'), None, _('Activate/Deactivate the Proxy'), self._toggle_active, True),
            ('TrapReq', gtk.STOCK_JUMP_TO, _('_Trap Requests'), None, _('Trap the requests or not'), self._toggle_trap, True),
        ])

        # Finish the toolbar
        self._uimanager.insert_action_group(actiongroup, 0)
        self._uimanager.add_ui_from_string(ui_proxy_menu)
        toolbar = self._uimanager.get_widget('/Toolbar')
        self.bt_drop = toolbar.get_nth_item(3)
        self.bt_send = toolbar.get_nth_item(4)
        self.bt_next = toolbar.get_nth_item(5)
        separat = toolbar.get_nth_item(6)
        #assert toolbar.get_n_items() == 4
        separat.set_draw(False)
        separat.set_expand(True)
        self.vbox.pack_start(toolbar, False)
        self.vbox.show()
        toolbar.show()
        # Request-response viewer
        self.reqresp = reqResViewer.reqResViewer(w3af,
                [self.bt_drop.set_sensitive, self.bt_send.set_sensitive],
                editableRequest=True)
        self.reqresp.set_sensitive(False)

        vbox = gtk.VBox()
        vbox.pack_start(self.reqresp, True, True)
        vbox.show()
        # Notebook
        self.nb = gtk.Notebook()
        # Intercept
        tmp = gtk.Label(_("_Intercept"))
        tmp.set_use_underline(True)
        self.nb.append_page(vbox, tmp)
        # History
        self.httplog = httpLogTab.httpLogTab(w3af, time_refresh=True)
        tmp = gtk.Label(_("_History"))
        tmp.set_use_underline(True)
        self.nb.append_page(self.httplog, tmp)
        # Options
        self._initOptions()
        self.vbox.pack_start(self.nb, True, True, padding=self.def_padding)
        self.nb.show()
        # Status bar for messages
        self.status_bar = gtk.Statusbar()
        self.vbox.pack_start(self.status_bar, False, False)
        self.status_bar.show()
        self.proxy = None
        # Finish it
        try:
            ipport = self.proxyoptions.ipport.getValue()
            ip, port = ipport.split(":")
            self._startProxy(ip, port)
        except w3afProxyException:
            # Ups, port looks already used..:(
            # Let's show alert and focus Options tab
            self.w3af.mainwin.sb(_("Failed to start local proxy"))
            self.fuzzable = None
            self.waitingRequests = False
            self.keepChecking = False
            self.nb.set_current_page(2)
        else:
            self.fuzzable = None
            self.waitingRequests = True
            self.keepChecking = True
        gobject.timeout_add(200, self._superviseRequests)
        self.show()

    def _initOptions(self):
        '''Init options.'''
        self.like_initial = True
        # Config options
        self.proxyoptions = ProxyOptions()
        self.proxyoptions.append("ipport",
                Option(_("Where to listen"), "localhost:8080", "IP:port",
                "ipport", _("IP and port where to listen")))
        self.proxyoptions.append("trap",
                Option(_("What to trap"), ".*", _("URLs to trap"), "regex",
                _("Regular expression that indicates what URLs to trap")))
        self.proxyoptions.append("methodtrap",
                Option(_("What methods to trap"), "GET,POST",
                    _("Methods to trap"), "list", _("Common separated methods. Left this field empty to trap all methods.")))
        self.proxyoptions.append("notrap",
                Option(_("What not to trap"), ".*\.(gif|jpg|png|css|js|ico|swf|axd|tif)$", _("URLs not to trap"), "regex",
                _("Regular expression that indicates what URLs not to trap")))
        self.proxyoptions.append("fixlength",
                Option("Fix content length", False, "Fix content length", "boolean"))

        self._previous_ipport = self.proxyoptions.ipport.getValue()
        optionBox = gtk.VBox()
        optionBox.show()
        # buttons and config panel
        buttonsArea = gtk.HBox()
        buttonsArea.show()
        saveBtn = gtk.Button(_("Save configuration"))
        saveBtn.show()
        rvrtBtn = gtk.Button(_("Revert to previous configuration"))
        buttonsArea.pack_start(rvrtBtn, False, False, padding=self.def_padding)
        buttonsArea.pack_start(saveBtn, False, False, padding=self.def_padding)
        rvrtBtn.show()
        self._optionsPanel = ConfigOptions(self.w3af, self, self.proxyoptions.options, saveBtn, rvrtBtn)
        optionBox.pack_start(self._optionsPanel, False, False)
        optionBox.pack_start(buttonsArea, False, False)
        tmp = gtk.Label(_("_Options"))
        tmp.set_use_underline(True)
        self.nb.append_page(optionBox, tmp)

    def configChanged(self, like_initial):
        """Propagates the change from the options.

        @params like_initial: If the config is like the initial one
        """
        self.like_initial = like_initial

    def reloadOptions(self):
        """Shutdown/Restart if needed."""
        new_ipport = self.proxyoptions.ipport.getValue()
        if new_ipport != self._previous_ipport:
            self.w3af.mainwin.sb(_("Stopping local proxy"))
            if self.proxy:
                self.proxy.stop()
            try:
                self._startProxy()
            except w3afProxyException:
                self.w3af.mainwin.sb(_("Failed to start local proxy"))
                return
        # rest of config
        try:
            self.proxy.setWhatToTrap(self.proxyoptions.trap.getValue())
            self.proxy.setWhatNotToTrap(self.proxyoptions.notrap.getValue())
            self.proxy.setMethodsToTrap(self.proxyoptions.methodtrap.getValue())
            self.proxy.setFixContentLength(self.proxyoptions.fixlength.getValue())
        except w3afException, w3:
            msg = _("Invalid configuration!\n" + str(w3))
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            opt = dlg.run()
            dlg.destroy()
        self._previous_ipport = new_ipport
        toolbar = self._uimanager.get_widget('/Toolbar')
        activeAction = toolbar.get_nth_item(0)
        activeAction.set_active(True)

    def _startProxy(self, ip=None, port=None, silent=False):
        """Starts the proxy."""
        if not ip:
            ipport = self.proxyoptions.ipport.getValue()
            ip, port = ipport.split(":")
        self.w3af.mainwin.sb(_("Starting local proxy"))

        try:
            self.proxy = localproxy.localproxy(ip, int(port))
        except w3afProxyException, w3:
            if not silent:
                msg = _(str(w3))
                dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
                opt = dlg.run()
                dlg.destroy()
            raise w3
        else:
            self.proxy.start2()

    def _superviseRequests(self, *a):
        """Supervise if there're requests to show.

        @return: True to gobject to keep calling it, False when all is done.
        """
        if self.waitingRequests:
            req = self.proxy.getTrappedRequest()
            if req is not None:
                self.waitingRequests = False
                self.fuzzable = req
                self.reqresp.request.set_sensitive(True)
                self.reqresp.request.showObject(req)
                self.bt_drop.set_sensitive(True)
        return self.keepChecking

    def _drop(self, widg):
        """Discards the actual request.

        @param widget: who sent the signal.
        """
        self.reqresp.request.clearPanes()
        self.reqresp.request.set_sensitive(False)
        self.waitingRequests = True
        self.proxy.dropRequest(self.fuzzable)

    def _send(self, widg):
        """Sends the request through the proxy.

        @param widget: who sent the signal.
        """
        request = self.reqresp.request.getObject()
        headers = request.dumpRequestHead()
        data = request.getData()
        if data:
            data = str(data)
        try:
            httpResp = helpers.coreWrap(self.proxy.sendRawRequest, self.fuzzable, headers, data)
        except w3afException:
            return
        else:
            self.fuzzable = None
            self.reqresp.response.set_sensitive(True)
            self.reqresp.response.showObject(httpResp)
            self.reqresp.nb.next_page()
            self.bt_next.set_sensitive(True)
            self.bt_drop.set_sensitive(False)
            self.bt_send.set_sensitive(False)

    def _next(self, widg):
        """Moves to the next request.

        @param widget: who sent the signal.
        """
        self.reqresp.request.clearPanes()
        self.reqresp.request.set_sensitive(False)
        self.reqresp.response.clearPanes()
        self.reqresp.response.set_sensitive(False)
        self.bt_next.set_sensitive(False)
        self.waitingRequests = True

    def _close(self):
        """Closes everything."""
        self.keepChecking = False
        msg = _("Do you want to quit and close the proxy?")
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
        opt = dlg.run()
        dlg.destroy()
        if  opt != gtk.RESPONSE_YES:
            return False
        self.proxy.stop()
        return True

    def _toggle_active(self, widget):
        """Start/stops the proxy."""
        proxyactive = widget.get_active()
        if proxyactive:
            if not self.proxy.isRunning():
                try:
                    self._startProxy()
                except w3afProxyException:
                    self.w3af.mainwin.sb(_("Failed to start local proxy"))
        else:
            self.w3af.mainwin.sb(_("Stopping local proxy"))
            self.proxy.stop()

    def _toggle_trap(self, widget):
        """Toggle the trap flag."""
        trapactive = widget.get_active()
        self.proxy.setTrap(trapactive)

    def _help(self, action):
        """Shows the help."""
        helpfile = os.path.join(os.getcwd(), "readme/EN/gtkUiHTML/gtkUiUsersGuide.html#Using_the_Proxy")
        webbrowser.open("file://" + helpfile)


class ConfigOptions(gtk.VBox):
    """Only the options for configuration.

    @param w3af: The Core
    @param parentWidg: The parentWidg widget
    @param options: The options to configure.
    @param save_btn: The save button.
    @param rvrt_btn: The revert button.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af, parentWidg, options, save_btn, rvrt_btn):
        super(ConfigOptions,self).__init__()
        self.set_spacing(5)
        self.w3af = w3af
        self.parentWidg = parentWidg
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
        """This create the notebook with all the options.

        @return: The created notebook if more than one grouping
        """
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
                tab = _("General")
            label = gtk.Label(tab)
            prop = helpers.PropagateBufferPayload(self._changedLabelNotebook, label, tab)
            table = self._makeTable(options, prop)
            nb.append_page(table, label)
        nb.show()
        return nb

    def _makeTable(self, options, prop):
        """Creates the table in which the options are shown.

        @param options: The options to show
        @param prop: The propagation function for this options
        @return: The created table

        For each row, it will put:

            - the option label
            - the configurable widget (textentry, checkbox, etc.)
            - an optional button to get more help (if the help is available)

        Also, the configurable widget gets a tooltip for a small description.
        """
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
        """Adjust the save/revert buttons and alert the tree of the change.

        @param like_initial: if the widgets are modified or not.

        It only will be called if any widget changed its state, through
        a propagation buffer.
        """
        self.save_btn.set_sensitive(not like_initial)
        self.rvrt_btn.set_sensitive(not like_initial)
        self.parentWidg.like_initial = like_initial

    def _changedLabelNotebook(self, like_initial, label, text):
        if like_initial:
            label.set_text(text)
        else:
            label.set_markup("<b>%s</b>" % text)

    def _changedWidget(self, widg, like_initial):
        """Receives signal when a widget changed or not.

        @param widg: the widget who changed.
        @param like_initial: if it's modified or not

        Handles the boldness of the option label and then propagates
        the change.
        """
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
        """Shows a dialog with the help message of the config option.

        @param widg: the widget who generated the signal
        @param helpmsg: the message to show in the dialog
        """
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, helpmsg)
        dlg.set_title('Plugin help')
        dlg.run()
        dlg.destroy()

    def _savePanel(self, widg):
        """Saves the config changes to the plugins.

        @param widg: the widget who generated the signal

        First it checks if there's some invalid configuration, then gets the value of 
        each option and save them to the plugin.
        """
        # check if all widgets are valid
        invalid = []
        for opt in self.options:
            if hasattr(opt.widg, "isValid"):
                if not opt.widg.isValid():
                    invalid.append(opt.getName())
        if invalid:
            msg = _("The configuration can't be saved, there is a problem in the following parameter(s):\n\n")
            msg += "\n-".join(invalid)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title(_('Configuration error'))
            dlg.run()
            dlg.destroy()
            return

        # Get the value from the GTK widget and set it to the option object
        for opt in self.options:
            opt.setValue( opt.widg.getValue() )

        for opt in self.options:
            opt.widg.save()
        self.w3af.mainwin.sb(_("Configuration saved successfully"))
        self.parentWidg.reloadOptions()

    def _revertPanel(self, *vals):
        """Revert all widgets to their initial state."""
        for widg in self.widgets_status:
            widg.revertValue()
        self.w3af.mainwin.sb(_("The configuration was reverted to its last saved state"))
        self.parentWidg.reloadOptions()
