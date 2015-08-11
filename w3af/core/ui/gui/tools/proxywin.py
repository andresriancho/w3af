"""
proxywin.py

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

from w3af.core.ui.gui import helpers, entries, httpLogTab
from w3af.core.ui.gui.reqResViewer import ReqResViewer
from w3af.core.ui.gui.entries import ConfigOptions, StatusBar

from w3af.core.controllers.daemons.proxy import InterceptProxy
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              ProxyException)

from w3af.core.data.options import option_types 
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList

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

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af):
        """Constructor."""
        super(ProxiedRequests, self).__init__(w3af, 'proxytool',
                                              _('w3af - Proxy'),
                                              'Using_the_Proxy',
                                              onDestroy=self._close)
        self.w3af = w3af
        
        self.def_padding = 5
        
        self._uimanager = gtk.UIManager()
        accelgroup = self._uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')
        actiongroup.add_actions([
            ('Help', gtk.STOCK_HELP, _(
                '_Help'), None, _('Help regarding this window'), self.open_help),
            ('Drop', gtk.STOCK_CANCEL, _('_Drop Request'),
             None, _('Drop request'), self._drop),
            ('Send', gtk.STOCK_YES, _('_Send Request'), None,
             _('Send request'), self._send),
            ('Next', gtk.STOCK_GO_FORWARD, _('_Next Request'),
             None, _('Move to the next request'), self._next),
        ])
        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip,
            # callback, initial_flag
            (
                'TrapReq', gtk.STOCK_JUMP_TO, _(
                    '_Trap Requests'), None, _('Trap requests'),
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
        self._init_options()
        self._prev_ip_port = None
        # We need to make widget (split or tabbed) firstly
        self._layout = self.pref.get_value('proxy', 'trap_view')
        self.reqresp = ReqResViewer(w3af, [self.bt_drop.set_sensitive,
                                           self.bt_send.set_sensitive],
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
        self.nb.set_current_page(
            tabs.index(self.pref.get_value('proxy', 'home_tab')))
        
        # Status bar for messages
        self.status_bar = StatusBar()
        self.vbox.pack_start(self.status_bar, False, False)
        self.status_bar.show()
        
        self.proxy = None
        
        # Finish it
        self.fuzzable = None
        self.waiting_requests = False
        self.keep_checking = False
        self.reload_options()
        
        gobject.timeout_add(200, self._supervise_requests)
        self.show()

    def _init_options(self):
        """Init options."""
        self.like_initial = True
        self.pref = ConfigOptions(self.w3af, self, 'proxy_options')
        
        # Proxy options
        proxy_options = OptionList()
        
        d = _('Proxy IP address and port number')
        h = _('Local IP address where the proxy will listen for HTTP requests.')
        o = opt_factory('ipport', '127.0.0.1:8080', d, option_types.IPPORT,
                        help=h)
        proxy_options.add(o)
        
        d = _('Regular expression for URLs to intercept')
        h = _('Regular expression to match against the URLs of HTTP requests'
              ' to decide if the request should be intercepted for analysis/'
              'modifications or not.')
        o = opt_factory('trap', ".*", d, option_types.REGEX, help=h)
        proxy_options.add(o)
        
        d = _("HTTP methods to intercept")
        h = _('Comma separated list of HTTP methods to intercept')
        o = opt_factory('methodtrap', "GET,POST", d, option_types.LIST, help=h)
        proxy_options.add(o)

        d = _("Ignored extensions")
        h = _('Filename extensions that will NOT be intercepted')
        default_value = ".*\.(gif|jpg|png|css|js|ico|swf|axd|tif)$"
        o = opt_factory("notrap", default_value, d, option_types.REGEX, help=h)
        proxy_options.add(o)

        d = _("View mode for intercept tab")
        views = ('Split', 'Tabbed')
        o = opt_factory("trap_view", views, d, option_types.COMBO)
        proxy_options.add(o)
        
        d = _("Home tab")
        homes = ['Intercept', 'History', 'Options']
        o = opt_factory("home_tab", homes, d, option_types.COMBO)
        proxy_options.add(o)
        
        self.pref.add_section('proxy', _('Proxy options'), proxy_options)
        
        # HTTP editor options
        editor_options = OptionList()
        
        o = opt_factory("wrap", True, _("Wrap long lines"), "boolean")
        editor_options.add(o)
        
        o = opt_factory("highlight_current_line", True,
                        _("Highlight current line"), "boolean")
        editor_options.add(o)
        
        o = opt_factory("highlight_syntax", True,
                        _("Highlight syntax"), "boolean")
        editor_options.add(o)
        
        o = opt_factory("display_line_num", True,
                        _("Display line numbers"), "boolean")
        editor_options.add(o)
        
        self.pref.add_section('editor', _('HTTP editor options'), editor_options)
        
        # Load values from configfile
        self.pref.load_values()
        self.pref.show()

    def config_changed(self, like_initial):
        """Propagates the change from the options.

        :param like_initial: If the config is like the initial one
        """
        self.like_initial = like_initial

    def reload_options(self):
        """Reload options.
            1. Stop proxy
            2. Try to start proxy with new params
            3. If can't => alert
            4. If everything is ok then start proxy
            5. Set Trap options
            6. Save options
        """
        new_port = self.pref.get_value('proxy', 'ipport')
        if new_port != self._prev_ip_port:
            self.w3af.mainwin.sb(_("Stopping local proxy"))
            if self.proxy:
                self.proxy.stop()
            
            try:
                self._start_proxy()
            except ProxyException:
                # Ups, port looks already used..:(
                # Let's show alert and focus Options tab
                self.w3af.mainwin.sb(_("Failed to start local proxy"))
                self.fuzzable = None
                self.waiting_requests = False
                self.keep_checking = False
                # Focus Options tab
                self.nb.set_current_page(2)
                return
            else:
                self.fuzzable = None
                self.waiting_requests = True
                self.keep_checking = True
        
        # Config test
        try:
            self.proxy.set_what_to_trap(self.pref.get_value('proxy', 'trap'))
            self.proxy.set_what_not_to_trap(self.pref.get_value('proxy', 'notrap'))
            self.proxy.set_methods_to_trap(self.pref.get_value('proxy', 'methodtrap'))
        except BaseFrameworkException, w3:
            self.show_alert(_("Invalid configuration!\n" + str(w3)))

        self._prev_ip_port = new_port
        httpeditor = self.reqresp.request.get_view_by_id('HttpRawView')
        httpeditor.set_show_line_numbers(self.pref.get_value('editor',
                                                             'display_line_num'))
        httpeditor.set_highlight_current_line(self.pref.get_value('editor',
                                                                  'highlight_current_line'))
        httpeditor.set_highlight_syntax(self.pref.get_value('editor',
                                                            'highlight_syntax'))
        httpeditor.set_wrap(self.pref.get_value('editor', 'wrap'))
        self.pref.save()

        if self._layout != self.pref.get_value('proxy', 'trap_view'):
            self.show_alert(_('Some of options will take effect after you'
                              ' restart proxy tool'))

    def show_alert(self, msg):
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
                                gtk.BUTTONS_OK, msg)
        dlg.run()
        dlg.destroy()

    def _start_proxy(self, ip=None, port=None, silent=False):
        """Starts the proxy."""
        if not ip:
            ipport = self.pref.get_value('proxy', 'ipport')
            ip, port = ipport.split(":")
            
        self.w3af.mainwin.sb(_("Starting local proxy"))
        
        try:
            self.proxy = InterceptProxy(ip, int(port), self.w3af.uri_opener)
        except ProxyException, w3:
            if not silent:
                self.show_alert(_(str(w3)))
            raise w3
        else:
            self.proxy.start()

    def _supervise_requests(self, *args):
        """Supervise if there are requests to show.

        :return: True to gobject to keep calling it, False when all is done.
        """
        if self.waiting_requests:
            req = self.proxy.get_trapped_request()
            if req is not None:
                self.waiting_requests = False
                self.fuzzable = req
                self.reqresp.request.set_sensitive(True)
                self.reqresp.request.show_object(req)
                self.bt_drop.set_sensitive(True)
                self.bt_send.set_sensitive(True)
                self.bt_next.set_sensitive(True)
        return self.keep_checking

    def _drop(self, widg):
        """Discards the actual request.

        :param widget: who sent the signal.
        """
        self.reqresp.request.clear_panes()
        self.reqresp.request.set_sensitive(False)
        self.waiting_requests = True
        self.proxy.drop_request(self.fuzzable)

    def _send(self, widg):
        """Sends the request through the proxy.

        :param widg: who sent the signal.
        """
        request = self.reqresp.request.get_object()
        # if nothing to send
        if not request:
            return

        headers = request.dump_request_head()
        data = request.get_data()

        if data:
            data = str(data)
        try:
            http_resp = helpers.coreWrap(self.proxy.on_request_edit_finished,
                                         self.fuzzable, headers, data)
        except BaseFrameworkException:
            return
        else:
            self.fuzzable = None
            self.reqresp.response.set_sensitive(True)
            self.reqresp.response.show_object(http_resp)
            self.reqresp.focus_response()
            self.bt_drop.set_sensitive(False)
            self.bt_send.set_sensitive(False)

    def _next(self, widg):
        """Moves to the next request.

        :param widg: who sent the signal.
        """
        resp = self.reqresp.response.get_object()
        # If there is request to send, let's send it first
        if not resp:
            self._send(None)
        self.reqresp.request.clear_panes()
        self.reqresp.request.set_sensitive(False)
        self.reqresp.response.clear_panes()
        self.reqresp.response.set_sensitive(False)
        self.bt_next.set_sensitive(False)
        self.reqresp.focus_request()
        self.waiting_requests = True

    def _close(self):
        """Closes everything."""
        self.keep_checking = False
        msg = _('Do you want to quit and close the proxy?')
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
        opt = dlg.run()
        dlg.destroy()
        if opt != gtk.RESPONSE_YES:
            return False
        
        if self.proxy:
            self.proxy.stop()
            
        return True

    def _toggle_trap(self, widget):
        """Toggle the trap flag."""
        if self.proxy is None:
            return

        trapactive = widget.get_active()
        self.proxy.set_trap(trapactive)
        
        status = 'Trap is %s' % ('on' if trapactive else 'off',)
        self.status_bar(status)
        
        # Send all requests in queue if Intercept is switched off
        if not trapactive:
            res = self.reqresp.response.get_object()
            req = self.reqresp.request.get_object()
            # If there is request to send, let's send it first
            if req and not res:
                self._send(None)

