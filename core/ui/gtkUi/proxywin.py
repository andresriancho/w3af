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
from core.data.options.comboOption import comboOption
from core.data.options.optionList import optionList
from core.controllers.daemons import localproxy
from core.ui.gtkUi.entries import ConfigOptions
import core.controllers.outputManager as om

ui_proxy_menu = """
<ui>
  <toolbar name="Toolbar">
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
            ('TrapReq', gtk.STOCK_JUMP_TO, _('_Trap Requests'), None, _('Trap the requests or not'),
                self._toggle_trap, False),
        ])
        # Finish the toolbar
        self._uimanager.insert_action_group(actiongroup, 0)
        self._uimanager.add_ui_from_string(ui_proxy_menu)
        toolbar = self._uimanager.get_widget('/Toolbar')
        self.bt_drop = toolbar.get_nth_item(2)
        self.bt_send = toolbar.get_nth_item(3)
        self.bt_next = toolbar.get_nth_item(4)
        self.bt_next.set_sensitive(False)
        self.bt_send.set_sensitive(False)
        self.bt_drop.set_sensitive(False)
        separat = toolbar.get_nth_item(5)
        separat.set_draw(False)
        separat.set_expand(True)
        self.vbox.pack_start(toolbar, False)
        self.vbox.show()
        toolbar.show()
        # Request-response viewer
        self._initOptions()
        self._prevIpport = None
        # We need to make widget (split or tabbed) firstly
        self._layout = self.pref.getValue('proxy', 'trap_view')
        self.reqresp = reqResViewer.reqResViewer(w3af,
                [self.bt_drop.set_sensitive, self.bt_send.set_sensitive],
                editableRequest=True, layout=self._layout)
        self.reqresp.set_sensitive(False)
        vbox = gtk.VBox()
        vbox.pack_start(self.reqresp, True, True)
        vbox.show()
        # Notebook
        self.nb = gtk.Notebook()
        tabs = []
        # Intercept
        tmp = gtk.Label(_("_Intercept"))
        tmp.set_use_underline(True)
        self.nb.append_page(vbox, tmp)
        tabs.append('Intercept')
        # History
        self.httplog = httpLogTab.httpLogTab(w3af, time_refresh=True)
        tmp = gtk.Label(_("_History"))
        tmp.set_use_underline(True)
        self.nb.append_page(self.httplog, tmp)
        tabs.append('History')
        # Options
        tmp = gtk.Label(_("_Options"))
        tmp.set_use_underline(True)
        self.nb.append_page(self.pref, tmp)
        tabs.append('Options')
        self.vbox.pack_start(self.nb, True, True, padding=self.def_padding)
        self.nb.show()
        # Go to Home Tab
        self.nb.set_current_page(tabs.index(self.pref.getValue('proxy', 'home_tab')))
        # Status bar for messages
        self.status_bar = gtk.Statusbar()
        self.vbox.pack_start(self.status_bar, False, False)
        self.status_bar.show()
        self.proxy = None
        # Finish it
        self.fuzzable = None
        self.waitingRequests = False
        self.keepChecking = False
        self.reloadOptions()
        gobject.timeout_add(200, self._superviseRequests)
        self.show()

    def _initOptions(self):
        '''Init options.'''
        self.like_initial = True
        self.pref = ConfigOptions(self.w3af, self, 'proxy_options')
        # Proxy options
        proxyOptions = optionList()
        proxyOptions.add(Option('ipport', "localhost:8080", "IP:port","ipport"))
        proxyOptions.add(Option('trap', ".*", _("URLs to trap"), "regex"))
        proxyOptions.add(Option('methodtrap', "GET,POST", _("Methods to trap"), "list"))
        proxyOptions.add(Option("notrap",
            ".*\.(gif|jpg|png|css|js|ico|swf|axd|tif)$", _("URLs not to trap"), "regex"))
        proxyOptions.add(Option("fixlength", True, _("Fix content length"), "boolean"))
        proxyOptions.add(comboOption("trap_view", ['Splitted', 'Tabbed'], _("View of Intercept tab"), "combo"))
        proxyOptions.add(comboOption("home_tab", ['Intercept', 'History', 'Options'], _("Home tab"), "combo"))
        self.pref.addSection('proxy', _('Proxy Options'), proxyOptions)
        # HTTP editor options
        editorOptions = optionList()
        editorOptions.add(Option("wrap", True, _("Wrap long lines"), "boolean"))
        editorOptions.add(Option("highlight_current_line", True, _("Highlight current line"), "boolean"))
        editorOptions.add(Option("highlight_syntax", True, _("Highlight syntax"), "boolean"))
        editorOptions.add(Option("display_line_num", True, _("Display line numbers"), "boolean"))
        self.pref.addSection('editor', _('HTTP Editor Options'), editorOptions)
        # Load values from configfile
        self.pref.loadValues()
        self.pref.show()

    def configChanged(self, like_initial):
        """Propagates the change from the options.

        @params like_initial: If the config is like the initial one
        """
        self.like_initial = like_initial

    def reloadOptions(self):
        """Reload options.
        1. Stop proxy
        2. Try to start proxy with new params
        3. If can't => alert
        4. If everything is ok then start proxy
        5. Set Trap options
        6. Save options
        """
        newPort = self.pref.getValue('proxy', 'ipport')
        if newPort != self._prevIpport:
            self.w3af.mainwin.sb(_("Stopping local proxy"))
            if self.proxy:
                self.proxy.stop()
            try:
                self._startProxy()
            except w3afProxyException:
                # Ups, port looks already used..:(
                # Let's show alert and focus Options tab
                self.w3af.mainwin.sb(_("Failed to start local proxy"))
                self.fuzzable = None
                self.waitingRequests = False
                self.keepChecking = False
                # Focus Options tab
                self.nb.set_current_page(2)
                return
            else:
                self.fuzzable = None
                self.waitingRequests = True
                self.keepChecking = True
        # Test of config
        try:
            self.proxy.setWhatToTrap(self.pref.getValue('proxy', 'trap'))
            self.proxy.setWhatNotToTrap(self.pref.getValue('proxy', 'notrap'))
            self.proxy.setMethodsToTrap(self.pref.getValue('proxy', 'methodtrap'))
            self.proxy.setFixContentLength(self.pref.getValue('proxy', 'fixlength'))
        except w3afException, w3:
            self.showAlert(_("Invalid configuration!\n" + str(w3)))

        self._prevIpport = newPort
        httpeditor = self.reqresp.request.getViewById('HttpRawView')
        httpeditor.set_show_line_numbers(self.pref.getValue('editor', 'display_line_num'))
        httpeditor.set_highlight_current_line(self.pref.getValue('editor', 'highlight_current_line'))
        httpeditor.set_highlight_syntax(self.pref.getValue('editor', 'highlight_syntax'))
        httpeditor.set_wrap(self.pref.getValue('editor', 'wrap'))
        self.pref.save()

        if self._layout != self.pref.getValue('proxy', 'trap_view'):
            self.showAlert(_("Some of options will take effect after you restart proxy tool"))

    def showAlert(self, msg):
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
        opt = dlg.run()
        dlg.destroy()

    def _startProxy(self, ip=None, port=None, silent=False):
        """Starts the proxy."""
        if not ip:
            ipport = self.pref.getValue('proxy', 'ipport')
            ip, port = ipport.split(":")
        self.w3af.mainwin.sb(_("Starting local proxy"))
        try:
            self.proxy = localproxy.localproxy(ip, int(port))
        except w3afProxyException, w3:
            if not silent:
                self.showAlert(_(str(w3)))
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
                self.bt_send.set_sensitive(True)
                self.bt_next.set_sensitive(True)
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
        # if nothing to send
        if not request:
            return
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
            self.reqresp.focusResponse()
            self.bt_drop.set_sensitive(False)
            self.bt_send.set_sensitive(False)

    def _next(self, widg):
        """Moves to the next request.

        @param widget: who sent the signal.
        """
        resp = self.reqresp.response.getObject()
        # If there is request to send, let's send it first
        if not resp:
            self._send(None)
        self.reqresp.request.clearPanes()
        self.reqresp.request.set_sensitive(False)
        self.reqresp.response.clearPanes()
        self.reqresp.response.set_sensitive(False)
        self.bt_next.set_sensitive(False)
        self.reqresp.focusRequest()
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
        if self.proxy:
            self.proxy.stop()
        return True

    def _toggle_trap(self, widget):
        """Toggle the trap flag."""
        trapactive = widget.get_active()
        self.proxy.setTrap(trapactive)
        # Send all requests in queue if Intercept is switched off
        if not trapactive:
            res = self.reqresp.response.getObject()
            req = self.reqresp.request.getObject()
            # If there is request to send, let's send it first
            if req and not res:
                self._send(None)

    def _help(self, action):
        """Shows the help."""
        helpfile = os.path.join(os.getcwd(), "readme/EN/gtkUiHTML/gtkUiUsersGuide.html#Using_the_Proxy")
        webbrowser.open("file://" + helpfile)
