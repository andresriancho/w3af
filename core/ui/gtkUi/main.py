'''
main.py

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
from __future__ import absolute_import

import pprint
import StringIO
import sys

# I perform the GTK UI dependency check here
# please note that there is also a CORE dependency check, which verifies the
# presence of different libraries.
# This task is done in different places because the consoleUi has different requirements
# than the GTK UI.
from . import dependencyCheck
dependencyCheck.gtkui_dependency_check()

# Now that I know that I have them, import them!
import pygtk
import gtk, gobject


# This is just general info, to help people knowing their system
print "Starting w3af, running on:"
print "  Python version:"
print "\n".join("    "+x for x in sys.version.split("\n"))
print "  GTK version:", ".".join(str(x) for x in gtk.gtk_version)
print "  PyGTK version:", ".".join(str(x) for x in gtk.pygtk_version)
print

# Threading initializer
if sys.platform == "win32":
    gobject.threads_init()
else:
    gtk.gdk.threads_init()

# Load the theme (this fixes bug [ 2022433 ] windows buttons without images)
# https://sourceforge.net/tracker/index.php?func=detail&aid=2022433&group_id=170274&atid=853652
if sys.platform == "win32":
    gtk.rc_add_default_file('%USERPROFILE%/.gtkrc-2.0')

# splash!
from core.ui.gtkUi.splash import Splash
splash = Splash()

try:
    import sqlite3
except ImportError:
    # TODO: Why am I checking this here and not in the dependencyCheck?
    msg = 'You have to install the sqlite3 database module to be able to run the GTK user'
    msg += ' interface. On debian based distributions you should install: python-pysqlite2'
    print msg
    sys.exit( 1 )

import threading, shelve, os
import core.controllers.w3afCore
import core.controllers.miscSettings
from core.controllers.auto_update import VersionMgr, is_working_copy
from core.controllers.w3afException import w3afException
import core.data.kb.config as cf
import core.data.parsers.urlParser as urlParser
import core.controllers.outputManager as om
from . import scanrun, exploittab, helpers, profiles, craftedRequests, compare, exception_handler
from . import export_request
from . import entries, encdec, messages, logtab, pluginconfig, confpanel
from . import wizard, guardian, proxywin

from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.get_w3af_version import get_w3af_version

import webbrowser, time

MAINTITLE = "w3af - Web Application Attack and Audit Framework"

#    Commented out: this has no sense after Results reorganizing
#    <menu action="ViewMenuScan">
#      <menuitem action="URLWindow"/>
#      <menuitem action="KBExplorer"/>
#    </menu>
ui_menu = """
<ui>
  <menubar name="MenuBar">
    <menu action="ProfilesMenu">
      <menuitem action="New"/>
      <menuitem action="Save"/>
      <menuitem action="SaveAs"/>
      <menuitem action="Revert"/>
      <menuitem action="Delete"/>
      <menuitem action="Quit"/>
    </menu>
    <menu action="EditMenuScan">
      <menuitem action="EditPlugin"/>
    </menu>
    <menu action="ViewMenuExploit">
      <menuitem action="ExploitVuln"/>
      <menuitem action="Interactive"/>
    </menu>
    <menu action="ToolsMenu">
      <menuitem action="ManualRequest"/>
      <menuitem action="FuzzyRequest"/>
      <menuitem action="EncodeDecode"/>
      <menuitem action="ExportRequest"/>
      <menuitem action="Compare"/>
      <menuitem action="Proxy"/>
    </menu>
    <menu action="ConfigurationMenu">
      <menuitem action="URLconfig"/>
      <menuitem action="Miscellaneous"/>
    </menu>
    <menu action="HelpMenu">
      <menuitem action="Help"/>
      <menuitem action="Wizards"/>
      <separator name="s4"/>
      <menuitem action="About"/>
    </menu>
  </menubar>
  <toolbar name="Toolbar">
    <toolitem action="Wizards"/>
    <separator name="s5"/>
    <toolitem action="New"/>
    <toolitem action="Save"/>
    <separator name="s1"/>
    <toolitem action="StartStop"/>
    <toolitem action="Pause"/>
    <separator name="s2"/>
    <toolitem action="ExploitAll"/>
    <separator name="s3"/>
    <toolitem action="ManualRequest"/>
    <toolitem action="FuzzyRequest"/>
    <toolitem action="EncodeDecode"/>
    <toolitem action="ExportRequest"/>
    <toolitem action="Compare"/>
    <toolitem action="Proxy"/>
  </toolbar>
</ui>
"""

class FakeShelve(dict):
    def close(self):
        pass

class AboutDialog(gtk.Dialog):
    '''A dialog with the About information.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(AboutDialog,self).__init__(_("About..."), None, gtk.DIALOG_MODAL,
                      (_("Check the web site"),gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

        # content
        img = gtk.image_new_from_file('core/ui/gtkUi/data/splash.png')
        self.vbox.pack_start(img)
        version = get_w3af_version()
        self.label = gtk.Label(version)
        self.label.set_justify(gtk.JUSTIFY_CENTER)
        self.vbox.pack_start(self.label)

        # the home button
        self.butt_home = self.action_area.get_children()[1]
        self.butt_home.connect("clicked", self._goWeb)

        # the ok button
        self.butt_saveas = self.action_area.get_children()[0]
        self.butt_saveas.connect("clicked", lambda x: self.destroy())

        self.show_all()

    def _goWeb(self, w):
        '''Opens the web site and closes the dialog.'''
        try:
            webbrowser.open("http://w3af.sourceforge.net/")
        except Exception,  e:
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
            raise RuntimeError(_("BUG! The communicator was never initialized"))
        self.callback = e
        self.client = e

    def destroy(self):
        '''Destroys the window.'''
        self.isActive = False
        return True

    def create(self, info=None):
        '''Assures the window is shown.
        
        Create a new window if not active, raises the previous one if already 
        is created.

        @param info: info to sent initially to the window
        '''
        if self.isActive:
            self.client.present()
        else:
            self.winCreator(self.w3af, self)
            self.isActive = True
        if info is not None:
            self.send(info)
    __call__ = create

    def send(self, info):
        '''Sends information to the window.

        @param info: info to sent initially to the window
        '''
        if not self.isActive:
            self.create()
        self.callback(info)

    def enable(self, window, callback):
        '''Enables the window.'''
        self.client = window
        self.callback = callback

class MainApp(object):
    '''Main GTK application

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''

    def __init__(self, profile, do_upd):
        w3af_icon = 'core/ui/gtkUi/data/w3af_icon.png'
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_from_file(w3af_icon)
        self.window.connect("delete_event", self.quit)
        self.window.connect('key_press_event', self.helpF1)
        splash.push(_("Loading..."))
        
        if do_upd in (None, True) and is_working_copy():
            # Do SVN update stuff
            vmgr = VersionMgr(log=splash.push)
            
            #  Set callbacks
            def ask(msg):
                dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, 
                                gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
                dlg.set_icon_from_file(w3af_icon)
                opt = dlg.run()
                dlg.destroy()
                return opt == gtk.RESPONSE_YES
            vmgr.callback_onupdate_confirm = ask
            
            #  Event registration
            def notify(msg):
                dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, 
                                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, msg)
                dlg.set_icon_from_file(w3af_icon)
                dlg.run()
                dlg.destroy()
            vmgr.register(VersionMgr.ON_ACTION_ERROR, notify, 'Error occured.')
            msg = 'At least one new dependency was included in w3af. Please ' \
            'update manually.'
            vmgr.register(VersionMgr.ON_UPDATE_ADDED_DEP, notify, msg)
            
            #  If an error occurred and the error the result is None
            resp = vmgr.update(force=do_upd)
            if resp:
                files, lrev, rrev = resp
                if rrev:
                    tabnames=("Updated Files", "Latest Changes")
                    dlg = entries.TextDialog("Update report", 
                                             tabnames=tabnames,
                                             icon=w3af_icon)
                    dlg.addMessage(str(files), page_num=0)
                    dlg.addMessage(str(vmgr.show_summary(lrev, rrev)),
                                   page_num=1)
                    dlg.done()
                    dlg.dialog_run()

        # title and positions
        self.window.set_title(MAINTITLE)
        genconfigfile = os.path.join(get_home_dir(),  "generalconfig.pkl") 
        try:
            self.generalconfig = shelve.open(genconfigfile)
        except Exception, e:
            print "WARNING: something bad happened when trying to open the general config!"
            print "    File: %r" % genconfigfile
            print "    Problem:", e
            print 
            self.generalconfig = FakeShelve()
        self.window.resize(*self.generalconfig.get("mainwindow-size", (800, 600)))
        self.window.move(*self.generalconfig.get("mainwindow-position", (50, 50)))

        mainvbox = gtk.VBox()
        self.window.add(mainvbox)
        mainvbox.show()

        splash.push(_("Initializing core..."))
        self.w3af = core.controllers.w3afCore.w3afCore()
        
        # This is inited before all, to have a full logging facility.
        om.out.setOutputPlugins( ['gtkOutput'] )

        # status bar
        splash.push(_("Building the status bar..."))
        guard = guardian.FoundObjectsGuardian(self.w3af)
        self.sb = entries.StatusBar(_("Program started ok"), [guard])

        # Using print so the user can read this in the console, together with 
        # the GTK, python and pygtk versions.
        print '\n  '.join(get_w3af_version().split('\n'))

        self.w3af.mainwin = self
        self.isRunning = False
        self.paused = False
        self.scanShould = "start"
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
            ('Quit', gtk.STOCK_QUIT, _('_Quit'), None, _('Exit the program'), lambda w: self.quit(None, None)),
            ('New', gtk.STOCK_NEW, _('_New'), None, _('Create a new profile'), lambda w: self.profileAction("new")),
            ('Save', gtk.STOCK_SAVE, _('_Save'), None, _('Save this configuration'), lambda w: self.profileAction("save")),
            ('SaveAs', gtk.STOCK_SAVE_AS, _('Save _as...'), None, _('Save this configuration in a new profile'), lambda w: self.profileAction("saveAs")),
            ('Revert', gtk.STOCK_REVERT_TO_SAVED, _('_Revert'), None, _('Revert the profile to its saved state'), lambda w: self.profileAction("revert")),
            ('Delete', gtk.STOCK_DELETE, _('_Delete'), None, _('Delete this profile'), lambda w: self.profileAction("delete")),
            ('ProfilesMenu', None, _('_Profiles')),
            ('ViewMenuScan', None, _('_View')),
            ('ViewMenuExploit', None, _('_View')),
            
            ('EditPlugin', gtk.STOCK_EDIT, _('_Edit plugin'), None, _('Edit selected plugin'), self._editSelectedPlugin),
            ('EditMenuScan', None, _('_Edit'), None, _('Edit'), self._editMenu),
            
            ('URLconfig', None, _('_HTTP Config'), None, _('HTTP configuration'), self.menu_config_http),
            ('Miscellaneous', None, _('_Miscellaneous'), None, _('Miscellaneous configuration'), self.menu_config_misc),
            ('ConfigurationMenu', None, _('_Configuration')),
            
            ('ManualRequest', gtk.STOCK_INDEX, _('_Manual Request'), '<Control>m', _('Generate manual HTTP request'), self._manual_request),
            ('FuzzyRequest', gtk.STOCK_PROPERTIES, _('_Fuzzy Request'), '<Control>u', _('Generate fuzzy HTTP requests'), self._fuzzy_request),
            ('EncodeDecode', gtk.STOCK_CONVERT, _('Enc_ode/Decode'), '<Control>o', _('Encodes and Decodes in different ways'), self._encode_decode),
            ('ExportRequest', gtk.STOCK_COPY, _('_Export Request'), '<Control>e', _('Export HTTP request'), self._export_request),
            ('Compare', gtk.STOCK_ZOOM_100, _('_Compare'), '<Control>r', _('Compare different requests and responses'), self._compare),
            ('Proxy', gtk.STOCK_CONNECT, _('_Proxy'), '<Control>p', _('Proxies the HTTP requests, allowing their modification'), self._proxy_tool),
            ('ToolsMenu', None, _('_Tools')),

            ('Wizards', gtk.STOCK_SORT_ASCENDING, _('_Wizards'), None, _('Point & Click Penetration Test'), self._wizards),
            ('Help', gtk.STOCK_HELP, _('_Help'), None, _('Help regarding the framework'), self.menu_help),
            ('About', gtk.STOCK_ABOUT, _('_About'), None, _('About the framework'), self.menu_about),
            ('HelpMenu', None, _('_Help')),

            ('StartStop', gtk.STOCK_MEDIA_PLAY, _('_Start'), None, _('Start scan'), self._scan_director),
            ('ExploitAll', gtk.STOCK_EXECUTE, _('_Multiple Exploit'), None, _('Exploit all vulns'), self._exploit_all),
        ])

        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('Pause', gtk.STOCK_MEDIA_PAUSE, _('_Pause'), None, _('Pause scan'),
                           self._scan_pause, False),
        ])

#        Commented out: this has no sense after Results reorganizing
#        # the view menu for scanning
#        # (this is different to the others because this one is the first one)
#        actiongroup.add_toggle_actions([
#            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
#            ('KBExplorer', None, '_KB Explorer', None, 'Toggle the Knowledge Base Explorer',
#                           lambda w: self.dynPanels(w, "kbexplorer"), True),
#            ('URLWindow', None, '_URL Window', None, 'Toggle the URL Window', 
#                           lambda w: self.dynPanels(w, "urltree"), True),
#        ])
#        ag = actiongroup.get_action("ViewMenuScan")
#        ag.set_sensitive(False)
#        self.menuViews["Results"] = ag

        # the view menu for exploit
        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('ExploitVuln', None, '_Plugins', None, _('Toggle the plugins panel'),
                           lambda w: self.dynPanels(w, "exploitvuln"), True),
            ('Interactive', None, '_Shells and Proxies', None, _('Toggle the shells and proxies window'), 
                           lambda w: self.dynPanels(w, "interac"), True),
        ])
        ag = actiongroup.get_action("ViewMenuExploit")
        ag.set_sensitive(False)
        ag.set_visible(False)
        self.menuViews["Exploit"] = ag

        # the sensitive options for profiles
        self.profileActions = [actiongroup.get_action(x) for x in "Save SaveAs Revert Delete".split()]
        self.activateProfileActions([False,True,False,False])

        # the sensitive options for edit
        ag = actiongroup.get_action("EditPlugin")
        ag.set_sensitive(False)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(ui_menu)

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
        self.exploitallsens = helpers.SensitiveAnd(exploitall, ("stopstart", "tabinfo"))
        
        # tab dependant widgets
        self.tabDependant = [ (lambda x: self.exploitallsens.set_sensitive(x, "tabinfo"), ('Exploit',)),
                              (actiongroup.get_action("EditMenuScan").set_sensitive, ('Scan config')),
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
        self.helpChapter = ("Configuring_the_scan", "Running_the_scan", "--RESULTS--", "Exploitation")

        # notebook
        splash.push(_("Building the main screen..."))
        self.nb = gtk.Notebook()
        self.nb.connect("switch-page", self.nbChangedPage)
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
            # I handle this by creating the profiles without an initial profile selected
            # and by reporting it to the user in a toolbar
            self.profiles = profiles.ProfileList(self.w3af, initial=None)
            self.sb( str(ve) )
            
        pan.pack1(self.profiles)
        pan.pack2(self.pcbody)
        pan.show_all()
        label = gtk.Label(_("Scan config"))
        self.nb.append_page(pan, label)
        self.viewSignalRecipient = self.pcbody

        # dummy tabs creation for notebook, real ones are done in setTabs
        self.notetabs = {}
        for title in (_("Log"),_("Results"), _("Exploit")):
            dummy = gtk.Label("dummy")
            self.notetabs[title] = dummy
            self.nb.append_page(dummy, gtk.Label())
        self.setTabs(False)
        
        # status bar
        mainvbox.pack_start(self.sb, False)

        # communication between different windows
        self.commCompareTool = WindowsCommunication(self.w3af, compare.Compare)

        # finish it
        self.window.show()
        splash.destroy()
        gtk.main()

    def profileChanged(self, *args, **kwargs):
        if hasattr(self, "profiles"):
            self.profiles.profileChanged(*args, **kwargs)

    def _editMenu( self, widget ):
        '''
        This handles the click action of the user over the edit menu.
        The main objective of this function is to disable the "Edit Plugin" option, if the user isn't focused over a plugin.
        
        @parameter widget: Not used
        '''
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
        
    def _editSelectedPlugin( self, widget ):
        '''
        This is the handler for the "Edit Plugin" menu option.
        
        @parameter widget: Not used
        '''
        self.pcbody.editSelectedPlugin()
        
    def quit(self, widget, event, data=None):
        '''Main quit.

        @param widget: who sent the signal.
        @param event: the event that happened
        @param data: optional data to receive.
        '''
        msg = _("Do you really want to quit?")
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
        opt = dlg.run()
        dlg.destroy()

        if opt != gtk.RESPONSE_YES:
            return True
        helpers.endThreads()
        self.sb.clear()

        # saving windows config
        self.generalconfig["mainwindow-size"] = self.window.get_size()
        self.generalconfig["mainwindow-position"] = self.window.get_position()
        self.generalconfig.close()
        gtk.main_quit()
        time.sleep(0.5)
        self.w3af.stop()
        self.w3af.quit()
        return False

    def _scan_director(self, widget):
        '''Directs what to do with the Scan.'''
        action = "_scan_" + self.scanShould
        func = getattr(self, action)
        func()

    def saveStateToCore(self, relaxedTarget=False):
        '''Save the actual state to the core.

        @param relaxedTarget: if True, return OK even if the target wasn't saved ok
        @return: True if all went ok
        '''
        # Clear everything
        for ptype in self.w3af.getPluginTypes():
            self.w3af.setPlugins([], ptype)
        
        # save the activated plugins
        for ptype,plugins in self.pcbody.getActivatedPlugins():
            self.w3af.setPlugins(plugins, ptype)

        # save the URL, the rest of the options are saved in the "Advanced" dialog
        options = self.w3af.target.getOptions()
        url = self.pcbody.target.get_text()
        options['target'].setValue( url )
        if relaxedTarget:
            try:
                self.w3af.target.setOptions(options)
            except:
                pass
            return True
        try:
            helpers.coreWrap(self.w3af.target.setOptions, options)
        except w3afException:
            return False
        return True
        

    def _scan_start(self):
        '''Starts the actual scanning.

        @param widget: the widget that generated the signal.
        '''
        if not self.saveStateToCore():
            return
        
        # Verify that everything is ready to run
        try:
            helpers.coreWrap(self.w3af.initPlugins)
            helpers.coreWrap(self.w3af.verifyEnvironment)
        except w3afException:
            return

        def startScanWrap():
            try:
                self.w3af.start()
            except KeyboardInterrupt:
                # print 'Ctrl+C found, exiting!'
                pass
            except Exception:
                gobject.idle_add(self._scan_stopfeedback)
                
                def pprint_plugins():
                    # Return a pretty-printed string from the plugins dicts
                    import copy
                    from itertools import chain
                    plugs_opts = copy.deepcopy(self.w3af._pluginsOptions)
                    plugs = self.w3af._strPlugins

                    for ptype, plist in plugs.iteritems():
                        for p in plist:
                            if p not in chain(*(pt.keys() for pt in \
                                                    plugs_opts.itervalues())):
                                plugs_opts[ptype][p] = {}
                    
                    plugins = StringIO.StringIO()
                    pprint.pprint(plugs_opts, plugins)
                    return  plugins.getvalue()
                
                plugins_str = pprint_plugins()
                try:
                    exc_class, exc_inst, exc_tb = sys.exc_info()
                    exception_handler.handle_crash(exc_class, exc_inst,
                                                   exc_tb, plugins=plugins_str)
                finally:
                    del exc_tb
        
        # start real work in background, and start supervising if it ends                
        threading.Thread(target=startScanWrap).start()
        gobject.timeout_add(500, self._scan_superviseStatus)

        self.sb(_("The scan has started"))
        self.setTabs(True)
        self.throbber.running(True)
        self.toolbut_pause.set_sensitive(True)
        self.startstopbtns.changeInternals("Stop", gtk.STOCK_MEDIA_STOP, _("Stop scan"))
        self.scanShould = "stop"
        self.stoppedByUser = False
        self.nb.set_current_page(1)
        self.exploitallsens.set_sensitive(True, "stopstart")

        # Save the target URL to the history
        self.pcbody.target.insertURL()

        # sets the title 
        targets = cf.cf.getData('targets')
        if targets:
            target_domain = urlParser.getDomain(targets[0])
            self.window.set_title("w3af - " + target_domain)

    def _scan_pause(self, widget):
        '''Pauses the scan.'''
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
        '''Stops the scanning.'''
        self.w3af.stop()
        self.startstopbtns.set_sensitive(False)
        self.toolbut_pause.set_sensitive(False)
        self.sb(_("Stopping the scan..."), 15)
        self.stoppedByUser = True

    def _scan_stopfeedback(self):
        '''Visual elements when stopped.

        This is separated because it's called when the process finishes by
        itself or by the user click.
        '''
        self.startstopbtns.changeInternals(_("Clear"), gtk.STOCK_CLEAR, _("Clear all the obtained results"))
        self.throbber.running(False)
        self.toolbut_pause.set_sensitive(False)
        self.scanShould = "clear"
        self.startstopbtns.set_sensitive(True)
        if self.stoppedByUser:
            self.sb(_("The scan has stopped by user request"))
        else:
            self.sb(_("The scan has finished"))

    def _scan_clear(self):
        '''Clears core and gtkUi, and fixes button to next step.'''
        # cleanup
        self.nb.set_current_page(0)
        self.w3af.cleanup()
        messages.getQueueDiverter(reset=True)
        self.setTabs(False)
        self.sb(_("Scan results cleared"))
        self.exploitallsens.set_sensitive(False, "stopstart")

        # put the button in start
        self.startstopbtns.changeInternals(_("Start"), gtk.STOCK_MEDIA_PLAY, _("Start scan"))
        self.scanShould = "start"
        self.window.set_title(MAINTITLE)
        
        # This is inited before all, to have a full logging facility.
        om.out.setOutputPlugins( ['gtkOutput'] )

    def _scan_superviseStatus(self):
        '''Handles the waiting until core actually stopped.

        @return: True to be called again
        '''
        if self.w3af.isRunning():
            return True

        if self.paused:
            # stop checking, but don't change any feedback, only
            # turn on the pause button
            self.toolbut_pause.set_sensitive(True)
            return True

        # core is stopped, we had it in on, stop all
        self._scan_stopfeedback()
        return False


    def setTabs(self, sensit):
        '''Set the exploits tabs to real window or dummies labels. 
        
        @param sensit: if it's active or not
        '''
        # the View menu
        for menu in self.menuViews.values():
            menu.set_sensitive(sensit)
        self.isRunning = sensit

        # ok, the tabs, :p
        self._setTab(sensit, _("Log"),     logtab.LogBody)
        self._setTab(sensit, _("Results"), scanrun.ScanRunBody)
        self._setTab(sensit, _("Exploit"), exploittab.ExploitBody)

    def _setTab(self, sensit, title, realWidget):
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
        '''Configure HTTP options.'''
        configurable = self.w3af.uriOpener.settings
        confpanel.ConfigDialog(_("Configure HTTP settings"), self.w3af, configurable)

    def menu_config_misc(self, action):
        '''Configure Misc options.'''
        configurable = core.controllers.miscSettings.miscSettings()
        confpanel.ConfigDialog(_("Configure Misc settings"), self.w3af, configurable)

    def dynPanels(self, widget, panel):
        '''Turns on and off the Log Panel.'''
        active = widget.get_active()
        self.viewSignalRecipient.togglePanels(panel, active)

    def nbChangedPage(self, notebook, page, page_num):
        '''Changed the page in the Notebook.
        
        It manages which View will be visible in the Menu, and
        to which recipient the signal of that View should be 
        directed.
        '''
        ch = notebook.get_nth_page(page_num)
        page = notebook.get_tab_label(ch).get_text()
        self.w3af.helpChapters["main"] = self.helpChapter[page_num]

        self.viewSignalRecipient = None
        for name,menu in self.menuViews.items():
            if name == page:
                menu.set_sensitive(self.isRunning)
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

    def profileAction(self, action):
        '''Do the action on the profile.'''
        methname = action + "Profile"
        method = getattr(self.profiles, methname)
        method()

    def activateProfileActions(self, newstatus):
        '''Activate profiles buttons.

        @param newstatus: if the profile changed or not.
        '''
        for opt,stt in zip(self.profileActions, newstatus):
            opt.set_sensitive(stt)

    def menu_help(self, action):
        '''Shows the help message.'''
        helpers.open_help()

    def menu_about(self, action):
        '''Shows the about message.'''
        dlg = AboutDialog(self.w3af)
        dlg.run()

    def _exploit_all(self, action):
        '''Exploits all vulns.'''
        exploitpage = self.notetabs[_("Exploit")]
        exploitpage.exploitAll()

    def _manual_request(self, action):
        '''Generate manual HTTP requests.'''
        craftedRequests.ManualRequests(self.w3af)
    
    def _export_request(self, action):
        '''Export HTTP requests to python, javascript, etc.'''
        export_request.export_request(self.w3af)

    def _fuzzy_request(self, action):
        '''Generate fuzzy HTTP requests.'''
        craftedRequests.FuzzyRequests(self.w3af)

    def _encode_decode(self, action):
        '''Generate fuzzy HTTP requests.'''
        encdec.EncodeDecode(self.w3af)

    def _compare(self, action):
        '''Generate fuzzy HTTP requests.'''
        self.commCompareTool.create()

    def _proxy_tool(self, action):
        '''Proxies the HTTP calls.'''
        self.setTabs(True)
        proxywin.ProxiedRequests(self.w3af)

    def _wizards(self, action):
        '''Execute the wizards machinery.'''
        wizard.WizardChooser(self.w3af)

    def helpF1(self, widget, event):
        if event.keyval != 65470: # F1, check: gtk.gdk.keyval_name(event.keyval)
            return

        chapter = self.w3af.helpChapters["main"]
        if chapter == "--RESULTS--":
            chapter = self.w3af.helpChapters["scanrun"] 

        helpers.open_help(chapter)

    
def main(profile, do_upd):
    MainApp(profile, do_upd)
