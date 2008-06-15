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

import sys

# I perform this dependency check here, and not in "core.controllers.misc.dependencyCheck" because
# these dependencies are *only* for the GTK user interface, and aren't used in any other place
try:
    import pygtk
    pygtk.require('2.0')
    import gtk, gobject
    assert gtk.pygtk_version >= (2, 12) 
except:
    print 'You have to install pygtk version >=2.12 to be able to run the GTK user interface. On Debian based distributions: apt-get install python-gtk2'
    sys.exit( 1 )

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

# splash!
from core.ui.gtkUi.splash import Splash
splash = Splash()

try:
    import buzhug
except:
    try:
        from extlib.buzhug.buzhug import Base
    except:
        print 'You have to install the buzhug database module to be able to run the GTK user interface. Available at: http://buzhug.sourceforge.net/'
        sys.exit( 1 )

import threading, shelve, os
import core.controllers.w3afCore
import core.controllers.miscSettings
from core.controllers.w3afException import w3afException
from . import scanrun, exploittab, helpers, profiles, craftedRequests, compare
from . import entries, encdec, messages, logtab, pluginconfig, confpanel
from core.controllers.misc.homeDir import getHomeDir
import webbrowser, time

#    Commented out: this has no sense after Results reorganizing
#    <menu action="ViewMenuScan">
#      <menuitem action="URLWindow"/>
#      <menuitem action="KBExplorer"/>
#    </menu>
ui_menu = """
<ui>
  <menubar name="MenuBar">
    <menu action="ProfilesMenu">
      <menuitem action="Save"/>
      <menuitem action="SaveAs"/>
      <menuitem action="Revert"/>
      <menuitem action="Delete"/>
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
      <menuitem action="Compare"/>
    </menu>
    <menu action="ConfigurationMenu">
      <menuitem action="URLconfig"/>
      <menuitem action="Miscellaneous"/>
    </menu>
    <menu action="HelpMenu">
      <menuitem action="Help"/>
      <menuitem action="About"/>
    </menu>
  </menubar>
  <toolbar name="Toolbar">
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
    <toolitem action="Compare"/>
  </toolbar>
</ui>
"""

class AboutDialog(gtk.Dialog):
    '''A dialog with the About information.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(AboutDialog,self).__init__("About...", None, gtk.DIALOG_MODAL,
                      ("Check the web site",gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))

        # content
        img = gtk.image_new_from_file('core/ui/gtkUi/data/splash.png')
        self.vbox.pack_start(img)
        version = w3af.getVersion()
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
        webbrowser.open("http://w3af.sourceforge.net/")
        self.destroy()


class WindowsCommunication(object):
    def __init__(self, w3af, winCreator):
        self.w3af = w3af
        self.winCreator = winCreator
        self.isActive = False
        def e(x):
            raise RuntimeError("BUG! The communicator was never initialized")
        self.callback = e
        self.client = e

    def destroy(self):
        self.isActive = False

    def create(self, info=None):
        if self.isActive:
            self.client.present()
        else:
            self.winCreator(self.w3af, self)
            self.isActive = True
        if info is not None:
            self.send(info)
    __call__ = create

    def send(self, info):
        if not self.isActive:
            self.create()
        self.callback(info)

    def enable(self, window, callback):
        self.client = window
        self.callback = callback


class MainApp(object):
    '''Main GTK application

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''

    def __init__(self, profile):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
        self.window.connect("delete_event", self.quit)
        splash.push("Loading...")

        # title and positions
        self.window.set_title("w3af - Web Application Attack and Audit Framework")
        genconfigfile = os.path.join(getHomeDir(),  "generalconfig.pkl") 
        self.generalconfig = shelve.open(genconfigfile)
        self.window.resize(*self.generalconfig.get("mainwindow-size", (800, 600)))
        self.window.move(*self.generalconfig.get("mainwindow-position", (50, 50)))

        mainvbox = gtk.VBox()
        self.window.add(mainvbox)
        mainvbox.show()

        # status bar
        splash.push("Building the status bar...")
        self.sb = helpers.StatusBar("Program started ok")

        splash.push("Initializing core...")
        self.w3af = core.controllers.w3afCore.w3afCore()

        # Using print so the user can read this in the console, together with the GTK, python and pygtk versions.
        print '\n  '.join(self.w3af.getVersion().split('\n'))

        self.w3af.mainwin = self
        self.isRunning = False
        self.paused = False
        self.scanShould = "start"
        self.menuViews = {}

        # Create a UIManager instance
        splash.push("Creating menu and toolbar...")
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)
        self._actiongroup = actiongroup = gtk.ActionGroup('UIManager')

        # Create actions
        actiongroup.add_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback
            ('Save', gtk.STOCK_SAVE, '_Save', None, 'Save this configuration', lambda w: self.profileAction("save")),
            ('SaveAs', gtk.STOCK_SAVE_AS, 'Save _as...', None, 'Save this configuration in a new profile', lambda w: self.profileAction("saveAs")),
            ('Revert', gtk.STOCK_REVERT_TO_SAVED, '_Revert', None, 'Revert the profile to its saved state', lambda w: self.profileAction("revert")),
            ('Delete', gtk.STOCK_DELETE, '_Delete', None, 'Delete this profile', lambda w: self.profileAction("delete")),
            ('ProfilesMenu', None, '_Profiles'),
            ('ViewMenuScan', None, '_View'),
            ('ViewMenuExploit', None, '_View'),
            
            ('EditPlugin', gtk.STOCK_EDIT, '_Edit plugin', None, 'Edit selected plugin', self._editSelectedPlugin),
            ('EditMenuScan', None, '_Edit', None, 'Edit', self._editMenu),
            
            ('URLconfig', None, '_HTTP Config', None, 'HTTP configuration', self.menu_config_http),
            ('Miscellaneous', None, '_Miscellaneous', None, 'Miscellaneous configuration', self.menu_config_misc),
            ('ConfigurationMenu', None, '_Configuration'),
            
            ('ManualRequest', gtk.STOCK_INDEX, '_Manual Request', None, 'Generate manual HTTP request', self._manual_request),
            ('FuzzyRequest', gtk.STOCK_PROPERTIES, '_Fuzzy Request', None, 'Generate fuzzy HTTP requests', self._fuzzy_request),
            ('EncodeDecode', gtk.STOCK_CONVERT, '_Encode/Decode', None, 'Encodes and Decodes in different ways', self._encode_decode),
            ('Compare', gtk.STOCK_ZOOM_100, '_Compare', None, 'Compare different requests and responses', self._compare),
            ('ToolsMenu', None, '_Tools'),

            ('Help', gtk.STOCK_HELP, '_Help', None, 'Help regarding the framework', self.menu_help),
            ('About', gtk.STOCK_ABOUT, '_About', None, 'About the framework', self.menu_about),
            ('HelpMenu', None, '_Help'),

            ('StartStop', gtk.STOCK_MEDIA_PLAY, '_Start', None, 'Start scan', self._scan_director),
            ('ExploitAll', gtk.STOCK_EXECUTE, '_Multiple Exploit', None, 'Exploit all vulns', self._exploit_all),
        ])

        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('Pause', gtk.STOCK_MEDIA_PAUSE, '_Pause', None, 'Pause scan',
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
            ('ExploitVuln', None, '_Plugins', None, 'Toggle the plugins panel',
                           lambda w: self.dynPanels(w, "exploitvuln"), True),
            ('Interactive', None, '_Shells and Proxies', None, 'Toggle the shells and proxies window', 
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
        assert toolbar.get_n_items() == 11
        toolbut_startstop = entries.ToolbuttonWrapper(toolbar, 2)
        self.startstopbtns.addWidget(toolbut_startstop)
        self.toolbut_pause = toolbar.get_nth_item(3)
        self.toolbut_pause.set_sensitive(False)
        self.scanok = helpers.PropagateBuffer(self.startstopbtns.set_sensitive)
        exploitall = toolbar.get_nth_item(5)
        self.exploitallsens = helpers.SensitiveAnd(exploitall, ("stopstart", "tabinfo"))
        
        # tab dependant widgets
        self.tabDependant = [ (lambda x: self.exploitallsens.set_sensitive(x, "tabinfo"), ('Exploit',)),
                              (actiongroup.get_action("EditMenuScan").set_sensitive, ('Scan config')),
                            ]

        # the throbber  
        splash.push("Building the throbber...")
        self.throbber = helpers.Throbber()
        separat = gtk.SeparatorToolItem()
        separat.set_draw(False)
        separat.set_expand(True)
        separat.show()
        toolbar.insert(separat, -1)
        toolbar.insert(self.throbber, -1)

        # notebook
        splash.push("Building the main screen...")
        self.nb = gtk.Notebook()
        self.nb.connect("switch-page", self.nbChangedPage)
        mainvbox.pack_start(self.nb, True)
        self.nb.show()

        # scan config tab
        pan = gtk.HPaned()
        self.pcbody = pluginconfig.PluginConfigBody(self, self.w3af)
        self.profiles = profiles.ProfileList(self.w3af, initial=profile)
        pan.pack1(self.profiles)
        pan.pack2(self.pcbody)
        pan.set_position(150)
        pan.show_all()
        label = gtk.Label("Scan config")
        self.nb.append_page(pan, label)
        self.viewSignalRecipient = self.pcbody

        # dummy tabs creation for notebook, real ones are done in setTabs
        self.notetabs = {}
        for title in ("Log","Results", "Exploit"):
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
        if path != None and len(path) > 1:
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
        msg = "Do you really want to quit?"
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
        self.w3af.quit()
        return False

    def _scan_director(self, widget):
        action = "_scan_" + self.scanShould
        func = getattr(self, action)
        func()

    def saveStateToCore(self, relaxedTarget=False):
        '''Save the actual state to the core.

        @param relaxedTarget: if True, return OK even if the target wasn't saved ok
        @return: True if all went ok
        '''
        # save the activated plugins
        for type,plugins in self.pcbody.getActivatedPlugins():
            self.w3af.setPlugins(plugins, type)

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
        except w3afException, w3:
            return

        def startScanWrap():
            try:
                self.w3af.start()
            except KeyboardInterrupt:
#                print 'Ctrl+C found, exiting!'
                pass
        
        # start real work in background, and start supervising if it ends                
        threading.Thread(target=startScanWrap).start()
        gobject.timeout_add(500, self._scan_superviseStatus)

        self.sb("The scan has started")
        self.setTabs(True)
        self.throbber.running(True)
        self.toolbut_pause.set_sensitive(True)
        self.startstopbtns.changeInternals("Stop", gtk.STOCK_MEDIA_STOP, "Stop scan")
        self.scanShould = "stop"
        self.stoppedByUser = False
        self.nb.set_current_page(1)
        self.exploitallsens.set_sensitive(True, "stopstart")

    def _scan_pause(self, widget):
        shall_pause = widget.get_active()

        # stop/start core and throbber
        self.w3af.pause(shall_pause)
        self.startstopbtns.set_sensitive(not shall_pause)
        self.toolbut_pause.set_sensitive(not shall_pause)
        self.throbber.running(not shall_pause)
        self.paused = shall_pause

        if not shall_pause:
            self.sb("Resuming the scan...")
            # start the status supervisor
            gobject.timeout_add(500, self._scan_superviseStatus)
        else:
            self.sb("The scan is paused")

    def _scan_stop(self):
        '''Stops the scanning.'''
        self.w3af.stop()
        self.startstopbtns.set_sensitive(False)
        self.toolbut_pause.set_sensitive(False)
        self.sb("Stopping the scan...", 15)
        self.stoppedByUser = True

    def _scan_stopfeedback(self):
        '''Visual elements when stopped.

        This is separated because it's called when the process finishes by
        itself or by the user click.
        '''
        self.startstopbtns.changeInternals("Clear", gtk.STOCK_CLEAR, "Clear all the obtained results")
        self.throbber.running(False)
        self.toolbut_pause.set_sensitive(False)
        self.scanShould = "clear"
        self.startstopbtns.set_sensitive(True)
        if self.stoppedByUser:
            self.sb("The scan has stopped by user request")
        else:
            self.sb("The scan has finished")

    def _scan_clear(self):
        '''Clears core and gtkUi, and fixes button to next step.'''
        # cleanup
        self.nb.set_current_page(0)
        self.w3af.cleanup()
        messages.getQueueDiverter(reset=True)
        self.setTabs(False)
        self.sb("Scan results cleared")
        self.exploitallsens.set_sensitive(False, "stopstart")

        # put the button in start
        self.startstopbtns.changeInternals("Start", gtk.STOCK_MEDIA_PLAY, "Start scan")
        self.scanShould = "start"

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
        self._setTab(sensit, "Log",     logtab.LogBody)
        self._setTab(sensit, "Results", scanrun.ScanRunBody)
        self._setTab(sensit, "Exploit", exploittab.ExploitBody)

    def _setTab(self, sensit, title, realWidget):
        # create title and window/label
        label = gtk.Label(title)
        if sensit:
            newone = realWidget(self.w3af)
        else:
            newone = gtk.Label("The scan has not started: no info yet")
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
        configurable = self.w3af.uriOpener.settings
        confpanel.ConfigDialog("Configure HTTP settings", self.w3af, configurable)

    def menu_config_misc(self, action):
        configurable = core.controllers.miscSettings.miscSettings()
        confpanel.ConfigDialog("Configure Misc settings", self.w3af, configurable)

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
        helpfile = os.path.join(os.getcwd(), "readme/w3afUsersGuide.html")
        webbrowser.open("file://" + helpfile)

    def menu_about(self, action):
        '''Shows the about message.'''
        dlg = AboutDialog(self.w3af)
        dlg.run()

    def _exploit_all(self, action):
        '''Exploits all vulns.'''
        exploitpage = self.notetabs["Exploit"]
        exploitpage.exploitAll()

    def _manual_request(self, action):
        '''Generate manual HTTP requests.'''
        craftedRequests.ManualRequests(self.w3af)

    def _fuzzy_request(self, action):
        '''Generate fuzzy HTTP requests.'''
        craftedRequests.FuzzyRequests(self.w3af)

    def _encode_decode(self, action):
        '''Generate fuzzy HTTP requests.'''
        encdec.EncodeDecode(self.w3af)

    def _compare(self, action):
        '''Generate fuzzy HTTP requests.'''
        self.commCompareTool.create()

        
    
def main(profile):
    MainApp(profile)
