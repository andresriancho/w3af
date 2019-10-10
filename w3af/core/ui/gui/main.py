"""
main.py

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
from __future__ import absolute_import

# Now that I know that I have them, import them!
import gtk
import gobject
import shelve
import os
import webbrowser
import time
import sys

from multiprocessing.dummy import Process

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf

from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.misc_settings import MiscSettings
from w3af.core.controllers.exceptions import BaseFrameworkException, ScanMustStopByUserRequest
from w3af.core.controllers.exception_handling.helpers import pprint_plugins, get_versions
from w3af.core.controllers.misc.home_dir import get_home_dir
from w3af.core.controllers.misc.get_w3af_version import get_w3af_version

from w3af.core.ui.gui import GUI_DATA_PATH
from w3af.core.ui.gui.splash import Splash
from w3af.core.ui.gui.disclaimer import DisclaimerController
from w3af.core.ui.gui.exception_handling import unhandled
from w3af.core.ui.gui.exception_handling import user_reports_bug
from w3af.core.ui.gui.constants import W3AF_ICON, MAIN_TITLE, UI_MENU
from w3af.core.ui.gui.output.gtk_output import GtkOutput
from w3af.core.ui.gui.auto_update.gui_updater import GUIUpdater
 
from w3af.core.ui.gui import scanrun, helpers, profiles, compare
from w3af.core.ui.gui import export_request
from w3af.core.ui.gui import entries, pluginconfig, confpanel
from w3af.core.ui.gui import wizard, guardian
from w3af.core.ui.gui.tools import encdec
from w3af.core.ui.gui.user_help.open_help import open_help
from w3af.core.ui.gui.tabs.log.main_body import LogBody
from w3af.core.ui.gui.tabs.exploit.main_body import ExploitBody
from w3af.core.ui.gui.tools.fuzzy_requests import FuzzyRequests
from w3af.core.ui.gui.tools.manual_requests import ManualRequests
from w3af.core.ui.gui.tools.proxywin import ProxiedRequests

# This is just general info, to help people know their system and report more
# complete bugs
print "Starting w3af, running on:"
print get_versions()

# pylint: disable=E1101
# Threading initializer
if sys.platform == "win32":
    gobject.threads_init()
    # Load the theme, this fixes bug 2022433: Windows buttons without images
    gtk.rc_add_default_file('%USERPROFILE%/.gtkrc-2.0')
else:
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter()
# pylint: enable=E1101

class FakeShelve(dict):
    def close(self):
        pass


class AboutDialog(gtk.Dialog):
    """A dialog with the About information.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af):
        super(
            AboutDialog, self).__init__(_("About..."), None, gtk.DIALOG_MODAL,
                                        (_("Check the web site"), gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OK, gtk.RESPONSE_OK))

        # content
        img = gtk.image_new_from_file(os.path.join(GUI_DATA_PATH, 'splash.png'))
        self.vbox.pack_start(img)
        version = get_w3af_version()
        self.label = gtk.Label(version)
        #self.label.set_justify(gtk.JUSTIFY_CENTER)
        self.vbox.pack_start(self.label)

        # the home button
        self.butt_home = self.action_area.get_children()[1]
        self.butt_home.connect("clicked", self._goWeb)

        # the ok button
        self.butt_saveas = self.action_area.get_children()[0]
        self.butt_saveas.connect("clicked", lambda x: self.destroy())

        self.show_all()

    def _goWeb(self, w):
        """Opens the web site and closes the dialog."""
        try:
            webbrowser.open("http://w3af.org/")
        except Exception:
            #
            #   This catches bug #2685576
            #   https://sourceforge.net/tracker2/?func=detail&atid=853652&aid=2685576&group_id=170274
            #
            #   Which seems to be related to:
            #   http://mail.python.org/pipermail/python-list/2004-July/269513.html
            #
            pass
        self.destroy()


class WindowsCommunication(object):
    def __init__(self, w3af, winCreator):
        self.w3af = w3af
        self.winCreator = winCreator
        self.isActive = False

        def e(x):
            raise RuntimeError(
                _("BUG! The communicator was never initialized"))
        self.callback = e
        self.client = e

    def destroy(self):
        """Destroys the window."""
        self.isActive = False
        return True

    def create(self, info=None):
        """Assures the window is shown.

        Create a new window if not active, raises the previous one if already
        is created.

        :param info: info to sent initially to the window
        """
        if self.isActive:
            self.client.present()
        else:
            self.winCreator(self.w3af, self)
            self.isActive = True
        if info is not None:
            self.send(info)
    __call__ = create

    def send(self, info):
        """Sends information to the window.

        :param info: info to sent initially to the window
        """
        if not self.isActive:
            self.create()
        self.callback(info)

    def enable(self, window, callback):
        """Enables the window."""
        self.client = window
        self.callback = callback


class MainApp(object):
    """Main GTK application

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """

    def __init__(self, profile, do_upd):
        disclaimer = DisclaimerController()
        if not disclaimer.accept_disclaimer():
            return
    
        # First of all, create the nice splash screen so we can show something
        # to the user while all the hard work is done on the background
        splash = Splash()

        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_from_file(W3AF_ICON)
        self.window.connect("delete_event", self.quit)
        self.window.connect('key_press_event', self.help_f1)
        
        # This is the way we track if the window is currently maximize or not
        self.is_maximized = False
        self.window.connect("window-state-event", self.on_window_state_event)
        
        splash.push(_("Loading..."))

        self.w3af = w3af_core = w3afCore()

        # Now we start the error handling
        unhandled.set_except_hook(w3af_core)

        # Please note that this doesn't block the Splash window since it will
        # (hopefully) call splash.push once every time it has made some
        # progress, thus calling the splash window mainloop() and handling any
        # pending events
        gui_upd = GUIUpdater(do_upd, splash.push)
        gui_upd.update()

        # title and positions
        self.window.set_title(MAIN_TITLE)
        genconfigfile = os.path.join(get_home_dir(), "gui_config.pkl")
        try:
            self.generalconfig = shelve.open(genconfigfile)
        except Exception, e:
            print ("WARNING: something bad happened when trying to open the"
                   " general config! File: %s. Problem: %s" % (genconfigfile, e))
            self.generalconfig = FakeShelve()

        window_size = self.generalconfig.get("mainwindow-size", (1024, 768))
        window_position = self.generalconfig.get("mainwindow-position", (0, 0))
        should_maximize = self.generalconfig.get("should-maximize", True)

        self.window.resize(*window_size)
        self.window.move(*window_position)
        if should_maximize:
            self.window.maximize()

        mainvbox = gtk.VBox()
        self.window.add(mainvbox)
        mainvbox.show()

        splash.push(_("Initializing core..."))

        # This is inited before all, to have a full logging facility.
        om.manager.set_output_plugin_inst(GtkOutput())

        # status bar
        splash.push(_("Building the status bar..."))
        guard = guardian.FoundObjectsGuardian(self.w3af)
        self.exceptions_sb = guardian.FoundExceptionsStatusBar(self.w3af)
        self.sb = entries.StatusBar(_("Program started"), [self.exceptions_sb,
                                                           guard])

        self.w3af.mainwin = self
        self.is_running = False
        self.paused = False
        self.scan_should = "start"
        self.stopped_by_user = False
        self.menuViews = {}

        # Create a UIManager instance
        splash.push(_("Creating menu and toolbar..."))
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)
        self._actiongroup = actiongroup = gtk.ActionGroup('UIManager')

        # Create actions
        actiongroup.add_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), None, _(
                'Exit the program'), lambda w: self.quit(None, None)),
            ('New', gtk.STOCK_NEW, _('_New'), None, _(
                'Create a new profile'), lambda w: self.profile_action("new")),
            ('Save', gtk.STOCK_SAVE, _('_Save'), None, _('Save this configuration'), lambda w: self.profile_action("save")),
            ('SaveAs', gtk.STOCK_SAVE_AS, _('Save _as...'), None, _('Save this configuration in a new profile'), lambda w: self.profile_action("save_as")),
            ('Revert', gtk.STOCK_REVERT_TO_SAVED, _('_Revert'), None, _('Revert the profile to its saved state'), lambda w: self.profile_action("revert")),
            ('Delete', gtk.STOCK_DELETE, _('_Delete'), None, _('Delete this profile'), lambda w: self.profile_action("delete")),
            ('ProfilesMenu', None, _('_Profiles')),
            ('ViewMenuScan', None, _('_View')),
            ('ViewMenuExploit', None, _('_View')),

            ('EditPlugin', gtk.STOCK_EDIT, _('_Edit plugin'),
             None, _('Edit selected plugin'), self._edit_selected_plugin),
            ('EditMenuScan', None, _('_Edit'), None, _('Edit'),
             self._editMenu),

            ('URLconfig', None, _('_HTTP Config'), None, _(
                'HTTP configuration'), self.menu_config_http),
            ('Miscellaneous', None, _('_Miscellaneous'), None,
             _('Miscellaneous configuration'), self.menu_config_misc),
            ('ConfigurationMenu', None, _('_Configuration')),

            ('ManualRequest', gtk.STOCK_INDEX, _('_Manual Request'), '<Control>m', _('Generate manual HTTP request'), self._manual_request),
            ('FuzzyRequest', gtk.STOCK_PROPERTIES, _('_Fuzzy Request'), '<Control>u', _('Generate fuzzy HTTP requests'), self._fuzzy_request),
            ('EncodeDecode', gtk.STOCK_CONVERT, _('Enc_ode/Decode'), '<Control>o', _('Encodes and Decodes in different ways'), self._encode_decode),
            ('ExportRequest', gtk.STOCK_COPY, _('_Export Request'),
             '<Control>e', _('Export HTTP request'), self._export_request),
            ('Compare', gtk.STOCK_ZOOM_100, _('_Compare'), '<Control>r',
             _('Compare different requests and responses'), self._compare),
            ('Proxy', gtk.STOCK_CONNECT, _('_Proxy'), '<Control>p',
             _('Proxies the HTTP requests, allowing their modification'),
             self._proxy_tool),
            ('ToolsMenu', None, _('_Tools')),

            ('Wizards', gtk.STOCK_SORT_ASCENDING, _('_Wizards'),
             None, _('Point & Click Penetration Test'), self._wizards),
            ('ReportBug', gtk.STOCK_SORT_ASCENDING, _(
                '_Report a Bug'), None, _('Report a Bug'), self.report_bug),
            ('Help', gtk.STOCK_HELP, _('_Help'), None, _(
                'Help regarding the framework'), self.menu_help),
            ('About', gtk.STOCK_ABOUT, _('_About'), None, _(
                'About the framework'), self.menu_about),
            ('HelpMenu', None, _('_Help')),

            ('StartStop', gtk.STOCK_MEDIA_PLAY, _('_Start'),
             None, _('Start scan'), self._scan_director),
            ('ExploitAll', gtk.STOCK_EXECUTE, _('_Multiple Exploit'),
             None, _('Exploit all vulns'), self._exploit_all),
        ])

        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback,
            # initial_flag
            ('Pause', gtk.STOCK_MEDIA_PAUSE, _('_Pause'),
             None, _('Pause scan'), self._scan_pause, False),
        ])

        # the view menu for exploit
        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback,
            # initial_flag
            ('ExploitVuln', None, '_Plugins', None,
             _('Toggle the plugins panel'),
             lambda w: self.dyn_panels(w, "exploitvuln"), True),

            ('Interactive', None, '_Shells and Proxies', None,
             _('Toggle the shells and proxies window'),
             lambda w: self.dyn_panels(w, "interac"), True),
        ])
        ag = actiongroup.get_action("ViewMenuExploit")
        ag.set_sensitive(False)
        ag.set_visible(False)
        self.menuViews["Exploit"] = ag

        # the sensitive options for profiles
        self.profile_actions = [actiongroup.get_action(
            x) for x in "Save SaveAs Revert Delete".split()]
        self.activate_profile_actions([False, True, False, False])

        # the sensitive options for edit
        ag = actiongroup.get_action("EditPlugin")
        ag.set_sensitive(False)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(UI_MENU)

        # menubar and toolbar
        menubar = uimanager.get_widget('/MenuBar')
        mainvbox.pack_start(menubar, False)
        toolbar = uimanager.get_widget('/Toolbar')
        mainvbox.pack_start(toolbar, False)

        # put both start/stop buttons inside the wrapper
        self.startstopbtns = helpers.BroadcastWrapper()

        # get toolbar items
        assert toolbar.get_n_items() == 16
        toolbut_startstop = entries.ToolbuttonWrapper(toolbar, 5)
        self.startstopbtns.addWidget(toolbut_startstop)
        self.toolbut_pause = toolbar.get_nth_item(6)
        self.toolbut_pause.set_sensitive(False)
        self.scanok = helpers.PropagateBuffer(self.startstopbtns.set_sensitive)
        exploitall = toolbar.get_nth_item(8)
        self.exploitallsens = helpers.SensitiveAnd(
            exploitall, ("stopstart", "tabinfo"))

        # tab dependent widgets
        self.tabDependant = [(
            lambda x: self.exploitallsens.set_sensitive(
                x, "tabinfo"), ('Exploit',)),
            (actiongroup.get_action("EditMenuScan")
             .set_sensitive, ('Scan config')),
        ]

        # the throbber
        splash.push(_("Building the throbber..."))
        self.throbber = helpers.Throbber()
        separat = gtk.SeparatorToolItem()
        separat.set_draw(False)
        separat.set_expand(True)
        separat.show()
        toolbar.insert(separat, -1)
        toolbar.insert(self.throbber, -1)

        # help structure
        self.w3af.helpChapters = dict(main="Configuring_the_scan",
                                      scanrun="Browsing_the_Knowledge_Base")
        self.helpChapter = ("Configuring_the_scan",
                            "Running_the_scan", "--RESULTS--", "Exploitation")

        # notebook
        splash.push(_("Building the main screen..."))
        self.nb = gtk.Notebook()
        self.nb.connect("switch-page", self.nb_changed_page)
        mainvbox.pack_start(self.nb, True)
        self.nb.show()

        # scan config tab
        pan = entries.RememberingHPaned(self.w3af, "pane-scanconfig", 150)
        self.pcbody = pluginconfig.PluginConfigBody(self, self.w3af)
        try:
            self.profiles = profiles.ProfileList(self.w3af, initial=profile)
        except ValueError, ve:
            # This is raised when the profile doesn't exist
            #
            # I handle this by creating the profiles without an initial profile
            # selected and by reporting it to the user in a toolbar
            self.profiles = profiles.ProfileList(self.w3af, initial=None)
            self.sb(str(ve))

        pan.pack1(self.profiles)
        pan.pack2(self.pcbody)
        pan.show_all()
        label = gtk.Label(_("Scan config"))
        self.nb.append_page(pan, label)
        self.viewSignalRecipient = self.pcbody
        
        self.notetabs = {}
        
        # dummy tabs creation for notebook, real ones are done in set_tabs
        for title in (_("Log"), _("Results")):
            dummy = gtk.Label("dummy")
            self.notetabs[title] = dummy
            self.nb.append_page(dummy, gtk.Label())
        self.set_tabs(False)

        label = gtk.Label(_("Exploit"))
        exploit_tab_body = ExploitBody(self.w3af)
        self.nb.append_page(exploit_tab_body, label)
        self.notetabs[_("Exploit")] = exploit_tab_body

        # status bar
        mainvbox.pack_start(self.sb, False)

        # communication between different windows
        self.commCompareTool = WindowsCommunication(self.w3af, compare.Compare)

        # finish it
        self.window.show()
        splash.destroy()
        self.exceptions_sb.hide_all()

        # No need to add a try/except here to catch KeyboardInterrupt since
        # it is already done in unhandled.handle_crash
        gtk.main()

    def profile_changed(self, *args, **kwargs):
        if hasattr(self, "profiles"):
            self.profiles.profile_changed(*args, **kwargs)

    def _editMenu(self, widget):
        """
        This handles the click action of the user over the edit menu.

        The main objective of this function is to disable the "Edit Plugin"
        option, if the user isn't focused over a plugin.

        :param widget: Not used
        """
        treeToUse = None
        if self.pcbody.out_plugin_tree.is_focus():
            treeToUse = self.pcbody.out_plugin_tree
        elif self.pcbody.std_plugin_tree.is_focus():
            treeToUse = self.pcbody.std_plugin_tree
        else:
            # No focus, we should keep the option disabled
            return None

        # We know that we have focus.... but... is the selection a plugin ?
        (path, column) = treeToUse.get_cursor()
        if path is not None and len(path) > 1:
            # Excellent! it is over a plugin!
            # enable the menu option
            ag = self._actiongroup.get_action("EditPlugin")
            ag.set_sensitive(True)

    def _edit_selected_plugin(self, widget):
        """
        This is the handler for the "Edit Plugin" menu option.

        :param widget: Not used
        """
        self.pcbody.edit_selected_plugin()

    def on_window_state_event(self, widget, event, data=None):
        mask = gtk.gdk.WINDOW_STATE_MAXIMIZED
        self.is_maximized = widget.get_window().get_state() & mask == mask
    
    def quit(self, widget, event, data=None):
        """Main quit.

        :param widget: who sent the signal.
        :param event: the event that happened
        :param data: optional data to receive.
        """
        msg = _("Do you really want to quit?")
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION,
                                gtk.BUTTONS_YES_NO, msg)
        opt = dlg.run()
        dlg.destroy()

        if opt != gtk.RESPONSE_YES:
            return True
        helpers.end_threads()
        self.sb.clear()

        try:
            # saving windows config
            w = self.window
            self.generalconfig["should-maximize"] = self.is_maximized
            self.generalconfig["mainwindow-size"] = w.get_size()
            self.generalconfig["mainwindow-position"] = w.get_position()
            self.generalconfig.close()
        finally:
            # We set the generalconfig to a fake shelve just in case other
            # windows are still open and want to get some data from it, this
            # prevents: "ValueError: invalid operation on closed shelf"
            #
            #       https://github.com/andresriancho/w3af/issues/2691
            #
            self.generalconfig = FakeShelve()

            # Quit the mainloop
            gtk.main_quit()
            time.sleep(0.5)
            self.w3af.quit()

            return False

    def _scan_director(self, widget):
        """Directs what to do with the Scan."""
        action = "_scan_" + self.scan_should
        func = getattr(self, action)
        func()

    def save_state_to_core(self, relaxedTarget=False):
        """Save the actual state to the core.

        :param relaxedTarget: if True, return OK even if the target wasn't
                              successfully saved
        :return: True if all went ok
        """
        # Clear everything
        for plugin_type in self.w3af.plugins.get_plugin_types():
            self.w3af.plugins.set_plugins([], plugin_type)

        # save the activated plugins
        for plugin_type, plugins in self.pcbody.get_activated_plugins():
            self.w3af.plugins.set_plugins(plugins, plugin_type)

        # save the URL, the rest of the options are saved in the "Advanced"
        # dialog
        options = self.w3af.target.get_options()

        # unicode str needed. pygtk works with 'utf8'
        url = self.pcbody.target.get_text().decode('utf8')
        target_option = options['target']
        if relaxedTarget:
            try:
                target_option.set_value(url)
                self.w3af.target.set_options(options)
            except:
                pass
            return True
        else:
            
            try:
                helpers.coreWrap(target_option.set_value, url)
                helpers.coreWrap(self.w3af.target.set_options, options)
            except BaseFrameworkException:
                return False
            
        return True

    def _scan_start(self):
        """
        Starts the actual scanning
        """
        if not self.save_state_to_core():
            return

        def real_scan_start():
            # Verify that everything is ready to run
            try:
                helpers.coreWrap(self.w3af.plugins.init_plugins)
                helpers.coreWrap(self.w3af.verify_environment)
            except BaseFrameworkException:
                return
            
            self.w3af.start()

        def start_scan_wrap():
            # Just in case, make sure we have a GtkOutput in the output manager
            # for the current scan
            om.manager.set_output_plugin_inst(GtkOutput())
            
            
            try:
                real_scan_start()
            except KeyboardInterrupt:
                # FIXME: Confirm: we should never get here because threads
                # send the KeyboardInterrupt to the main thread.
                pass
            except ScanMustStopByUserRequest:
                pass
            except Exception:
                #
                #    Exceptions generated by plugins are handled in
                #    ExceptionHandler
                #
                #    The only exceptions that can get here are the ones in the
                #    framework and UI itself.
                #
                plugins_str = pprint_plugins(self.w3af)
                exc_class, exc_inst, exc_tb = sys.exc_info()
                unhandled.handle_crash(self.w3af, exc_class, exc_inst,
                                       exc_tb, plugins=plugins_str)
            finally:
                gobject.idle_add(self._scan_stopfeedback)
                self._scan_finished()

        # Starting output manager to try to avoid bug
        # https://github.com/andresriancho/w3af/issues/997
        om.out.debug('Starting output manager')

        # start real work in background, and start supervising if it ends
        scanner = Process(target=start_scan_wrap, name='MainGTKScanner')
        scanner.daemon = True
        scanner.start()
        gobject.timeout_add(500, self._scan_superviseStatus)

        self.sb(_("The scan has started"))
        self.set_tabs(True)
        self.throbber.running(True)
        self.toolbut_pause.set_sensitive(True)
        self.startstopbtns.change_internals("Stop", gtk.STOCK_MEDIA_STOP,
                                            _("Stop scan"))
        self.scan_should = "stop"
        self.stopped_by_user = False
        self.nb.set_current_page(1)
        self.exploitallsens.set_sensitive(True, "stopstart")

        # Save the target URL to the history
        self.pcbody.target.insert_url()

        # sets the title
        targets = cf.cf.get('targets')
        if targets:
            target_domain_obj = targets[0]
            target_domain = target_domain_obj.get_domain()
            self.window.set_title("w3af - " + target_domain)

    def _scan_pause(self, widget):
        """Pauses the scan."""
        shall_pause = widget.get_active()

        # stop/start core and throbber
        self.w3af.pause(shall_pause)
        self.startstopbtns.set_sensitive(not shall_pause)
        self.toolbut_pause.set_sensitive(not shall_pause)
        self.throbber.running(not shall_pause)
        self.paused = shall_pause

        if not shall_pause:
            self.sb(_("Resuming the scan..."))
            # start the status supervisor
            gobject.timeout_add(500, self._scan_superviseStatus)
        else:
            self.sb(_("The scan is paused"))

    def _scan_stop(self):
        """Stops the scanning."""
        def stop_scan_wrap():
            try:
                self.w3af.stop()
            except Exception:
                #
                #    Exceptions generated by plugins are handled in
                #    ExceptionHandler
                #
                #    The only exceptions that can get here are the ones in the
                #    framework and UI itself.
                #
                plugins_str = pprint_plugins(self.w3af)
                exc_class, exc_inst, exc_tb = sys.exc_info()
                unhandled.handle_crash(self.w3af, exc_class, exc_inst,
                                       exc_tb, plugins=plugins_str)

        # start real work in background, and start supervising if it ends
        scan_stop = Process(target=stop_scan_wrap, name='ScanStopper')
        scan_stop.daemon = True
        scan_stop.start()
        
        self.startstopbtns.set_sensitive(False)
        self.toolbut_pause.set_sensitive(False)
        self.sb(_("Stopping the scan..."), 15)
        self.stopped_by_user = True

    def _scan_stopfeedback(self):
        """Visual elements when stopped.

        This is separated because it's called when the process finishes by
        itself or by the user click.
        """
        self.startstopbtns.change_internals(_("Clear"),
                                            gtk.STOCK_CLEAR,
                                            _("Clear all the obtained results"))
        self.throbber.running(False)
        self.toolbut_pause.set_sensitive(False)
        self.scan_should = "clear"
        self.startstopbtns.set_sensitive(True)
        if self.stopped_by_user:
            self.sb(_("The scan has stopped by user request"))
        else:
            self.sb(_("The scan has finished"))

    def _scan_finished(self):
        """
        This method is called when the scan finishes successfully of because
        of an exception.
        """
        # After the scan finishes, I want to be able to use the GtkOutput
        # features for exploitation
        om.manager.set_output_plugin_inst(GtkOutput())
        
        exception_list = self.w3af.exception_handler.get_unique_exceptions()
        if exception_list:
            # damn...
            self.sb(_("Scan finished with exceptions"))
            self.exceptions_sb.show_all(len(exception_list))

    def _scan_clear(self):
        """Clears core and gui, and fixes button to next step."""
        # cleanup
        self.nb.set_current_page(0)
        self.w3af.cleanup()
        self.set_tabs(False)
        self.sb(_("Scan results cleared"))
        self.exploitallsens.set_sensitive(False, "stopstart")

        # put the button in start
        self.startstopbtns.change_internals(
            _("Start"), gtk.STOCK_MEDIA_PLAY, _("Start scan"))
        self.scan_should = "start"
        self.window.set_title(MAIN_TITLE)

        # This is done here in order to keep the logging facility.
        om.manager.set_output_plugin_inst(GtkOutput())

    def _scan_superviseStatus(self):
        """Handles the waiting until core finishes the scan.

        :return: True to be called again
        """
        if self.w3af.status.is_running():
            return True

        if self.paused:
            # stop checking, but don't change any feedback, only
            # turn on the pause button
            self.toolbut_pause.set_sensitive(True)
            return True

        # core is stopped, we had it in on, stop all
        self._scan_stopfeedback()
        return False

    def set_tabs(self, sensit):
        """Set the exploits tabs to real window or dummies labels.

        :param sensit: if it's active or not
        """
        # the View menu
        for menu in self.menuViews.values():
            menu.set_sensitive(sensit)
        self.is_running = sensit

        # ok, the tabs, :p
        self._set_tab(sensit, _("Log"), LogBody)
        self._set_tab(sensit, _("Results"), scanrun.ScanRunBody)

    def _set_tab(self, sensit, title, realWidget):
        # create title and window/label
        label = gtk.Label(title)
        if sensit:
            newone = realWidget(self.w3af)
        else:
            newone = gtk.Label(_("The scan has not started: no info yet"))
            newone.show()
            label.set_sensitive(False)
            newone.set_sensitive(False)

        # remove old page and insert this one
        pointer = self.notetabs[title]
        pos = self.nb.page_num(pointer)
        self.nb.remove_page(pos)
        self.nb.insert_page(newone, label, pos)
        self.notetabs[title] = newone

    def menu_config_http(self, action):
        """Configure HTTP options."""
        configurable = self.w3af.uri_opener.settings
        confpanel.ConfigDialog(_("Configure HTTP settings"), self.w3af,
                               configurable)

    def menu_config_misc(self, action):
        """Configure Misc options."""
        configurable = MiscSettings()
        confpanel.ConfigDialog(
            _("Configure Misc settings"), self.w3af, configurable)

    def dyn_panels(self, widget, panel):
        """Turns on and off the Log Panel."""
        active = widget.get_active()

        if hasattr(self.viewSignalRecipient, 'toggle_panels'):
            self.viewSignalRecipient.toggle_panels(panel, active)

    def nb_changed_page(self, notebook, page, page_num):
        """Changed the page in the Notebook.

        It manages which View will be visible in the Menu, and
        to which recipient the signal of that View should be
        directed.
        """
        ch = notebook.get_nth_page(page_num)
        page = notebook.get_tab_label(ch).get_text()
        self.w3af.helpChapters["main"] = self.helpChapter[page_num]

        self.viewSignalRecipient = None
        for name, menu in self.menuViews.items():
            if name == page:
                menu.set_sensitive(self.is_running)
                menu.set_visible(True)
                self.viewSignalRecipient = self.notetabs[name]
            else:
                menu.set_visible(False)

        if page not in self.menuViews:
            # even when we don't have no view, we should put
            # anyone, but disabled
            fake = self.menuViews.items()[0][1]
            fake.set_sensitive(False)
            fake.set_visible(True)

        # generic tab dependant widgets
        for widg, where in self.tabDependant:
            widg(page in where)

    def profile_action(self, action):
        """Do the action on the profile."""
        methname = action + "_profile"
        method = getattr(self.profiles, methname)
        method()

    def activate_profile_actions(self, newstatus):
        """Activate profiles buttons.

        :param newstatus: if the profile changed or not.
        """
        for opt, stt in zip(self.profile_actions, newstatus):
            opt.set_sensitive(stt)

    def menu_help(self, action):
        """Shows the help message."""
        open_help()

    def menu_about(self, action):
        """Shows the about message."""
        dlg = AboutDialog(self.w3af)
        dlg.run()

    def report_bug(self, action):
        """Report bug to Sourceforge"""
        user_reports_bug.user_reports_bug()

    def _exploit_all(self, action):
        """Exploits all vulns."""
        exploitpage = self.notetabs[_("Exploit")]
        exploitpage.exploit_all()

    def _manual_request(self, action):
        """Generate manual HTTP requests."""
        ManualRequests(self.w3af)

    def _export_request(self, action):
        """Export HTTP requests to python, javascript, etc."""
        export_request.export_request(self.w3af)

    def _fuzzy_request(self, action):
        """Generate fuzzy HTTP requests."""
        FuzzyRequests(self.w3af)

    def _encode_decode(self, action):
        """Generate fuzzy HTTP requests."""
        encdec.EncodeDecode(self.w3af)

    def _compare(self, action):
        """Generate fuzzy HTTP requests."""
        self.commCompareTool.create()

    def _proxy_tool(self, action):
        """Proxies the HTTP calls."""
        self.set_tabs(True)
        ProxiedRequests(self.w3af)

    def _wizards(self, action):
        """Execute the wizards machinery."""
        wizard.WizardChooser(self.w3af)

    def help_f1(self, widget, event):
        if event.keyval != 65470:  # F1, check: gtk.gdk.keyval_name(event.keyval)
            return

        chapter = self.w3af.helpChapters["main"]
        if chapter == "--RESULTS--":
            chapter = self.w3af.helpChapters["scanrun"]

        open_help(chapter)


def main(profile, do_upd):
    MainApp(profile, do_upd)
