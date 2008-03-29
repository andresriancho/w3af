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

import sys

# I perform this dependency check here, and not in "core.controllers.misc.dependencyCheck" because
# these dependencies are *only* for the GTK user interface, and aren't used in any other place
try:
    import pygtk
    pygtk.require('2.0')
    import gtk, gobject
except:
    print 'You have to install pygtk version >=2 to be able to run the GTK user interface. On Debian based distributions: apt-get install python-gtk2'
    sys.exit( 1 )

try:
    import buzhug
except:
    try:
        from extlib.buzhug.buzhug import Base
    except:
        print 'You have to install the buzhug database module to be able to run the GTK user interface. Available at: http://buzhug.sourceforge.net/'
        sys.exit( 1 )

import threading
import core.controllers.w3afCore
import core.controllers.miscSettings
from core.controllers.w3afException import w3afException
import core.ui.gtkUi.scanrun as scanrun
import core.ui.gtkUi.exploittab as exploittab
import core.ui.gtkUi.httpLogTab as httpLogTab
import core.ui.gtkUi.helpers as helpers
import core.ui.gtkUi.profiles as profiles
import core.ui.gtkUi.entries as entries
import core.ui.gtkUi.messages as messages
import core.ui.gtkUi.logtab as logtab
import core.ui.gtkUi.pluginconfig as pluginconfig
import core.ui.gtkUi.confpanel as confpanel
from core.controllers.misc import parseOptions
    

ui_menu = """
<ui>
  <menubar name="MenuBar">
    <menu action="ProfilesMenu">
      <menuitem action="Save"/>
      <menuitem action="SaveAs"/>
      <menuitem action="Revert"/>
      <menuitem action="Delete"/>
    </menu>
    <menu action="ViewMenuScan">
      <menuitem action="URLWindow"/>
      <menuitem action="KBExplorer"/>
    </menu>
    <menu action="ViewMenuExploit">
      <menuitem action="ExploitVuln"/>
      <menuitem action="Interactive"/>
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
  </toolbar>
</ui>
"""


class Throbber(gtk.ToolButton):
    '''Creates the throbber widget.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        self.img_static = gtk.Image()
        self.img_static.set_from_file('core/ui/gtkUi/data/throbber_static.gif')
        self.img_static.show()
        self.img_animat = gtk.Image()
        self.img_animat.set_from_file('core/ui/gtkUi/data/throbber_animat.gif')
        self.img_animat.show()

        super(Throbber,self).__init__(self.img_static, "")
        self.set_sensitive(False)
        self.show()

    def running(self, spin):
        if spin:
            self.set_icon_widget(self.img_animat)
        else:
            self.set_icon_widget(self.img_static)

class MainApp:
    '''Main GTK application

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, profile):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
        self.window.connect("delete_event", self.quit)
        self.window.set_title("w3af - Web Application Attack and Audit Framework")
        self.window.resize(800, 600)
        mainvbox = gtk.VBox()
        self.window.add(mainvbox)
        mainvbox.show()

        self.w3af = core.controllers.w3afCore.w3afCore()
        self.w3af.mainwin = self
        self.isRunning = False
        self.paused = False
        self.scanShould = "start"
        self.menuViews = {}

        # Create a UIManager instance
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')

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
            ('URLconfig', None, '_HTTP Config', None, 'HTTP configuration', self.menu_config_http),
            ('Miscellaneous', None, '_Miscellaneous', None, 'Miscellaneous configuration', self.menu_config_misc),
            ('ConfigurationMenu', None, '_Configuration'),
            ('Help', None, '_Help', None, 'Help regarding the framework', self.notyet),
            ('About', None, '_About', None, 'About the framework', self.notyet),
            ('HelpMenu', None, '_Help'),
            ('StartStop', gtk.STOCK_MEDIA_PLAY, '_Start', None, 'Start scan', self._scan_director),
        ])

        # the view menu for scanning
        # (this is different to the others because this one is the first one)
        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('Pause', gtk.STOCK_MEDIA_PAUSE, '_Pause', None, 'Pause scan',
                           self._scan_pause, False),
            ('KBExplorer', None, '_KB Explorer', None, 'Toggle the Knowledge Base Explorer',
                           lambda w: self.dynPanels(w, "kbexplorer"), True),
            ('URLWindow', None, '_URL Window', None, 'Toggle the URL Window', 
                           lambda w: self.dynPanels(w, "urltree"), True),
        ])
        ag = actiongroup.get_action("ViewMenuScan")
        ag.set_sensitive(False)
        self.menuViews["Results"] = ag

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
        assert toolbar.get_n_items() == 4
        toolbut_startstop = entries.ToolbuttonWrapper(toolbar, 2)
        self.startstopbtns.addWidget(toolbut_startstop)
        self.toolbut_pause = toolbar.get_nth_item(3)
        self.toolbut_pause.set_sensitive(False)
        self.scanok = helpers.PropagateBuffer(self.startstopbtns.set_sensitive)

        # the throbber  
        self.throbber = Throbber()
        separat = gtk.SeparatorToolItem()
        separat.set_draw(False)
        separat.set_expand(True)
        separat.show()
        toolbar.insert(separat, -1)
        toolbar.insert(self.throbber, -1)

        # notebook
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
        for title in ("Results", "Log", "Exploit"):
            dummy = gtk.Label("dummy")
            self.notetabs[title] = dummy
            self.nb.append_page(dummy, gtk.Label())
        self.setTabs(False)
        
        # Request Response navigator
        self.httplog = httpLogTab.httpLogTab(self.w3af)
        label = gtk.Label("Request response navigator")
        #label.set_sensitive(False)
        #self.httplog.set_sensitive(False)
        self.nb.append_page(self.httplog, label)
        self.httplog.show()
  
        # status bar
        self.sb = helpers.StatusBar("Program started ok")
        mainvbox.pack_start(self.sb, False)

        self.window.show()
        helpers.init(self.window)
        gtk.main()

    def quit(self, widget, event, data=None):
        '''Main quit.

        @param widget: who sent the signal.
        @param event: the event that happened
        @param data: optional data to receive.
        '''
        helpers.endThreads()
        gtk.main_quit()
        return False

    def notyet(self, widget):
        '''Just a not yet implemented message to stdout.'''
        print "This functionality is not implemented yet!"


    def _scan_director(self, widget):
        action = "_scan_" + self.scanShould
        func = getattr(self, action)
        func()

    def _scan_start(self):
        '''Starts the actual scanning.

        @param widget: the widget that generated the signal.
        '''
        # save the activated plugins
        for type,plugins in self.pcbody.getActivatedPlugins():
            self.w3af.setPlugins(plugins, type)

        # save the URL, the rest of the options are saved in the "Advanced" dialog
        info = self.w3af.target.getOptionsXML()
        options = parseOptions.parseXML(info)
        url = self.pcbody.target.get_text()
        options['target'].update(default=url)
        try:
            helpers.coreWrap(self.w3af.target.setOptions, options)
        except w3afException:
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
        self.nb.set_current_page(1)

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
        self.sb("Stopping the scan...")

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
        self.sb("The scan has stopped")

    def _scan_clear(self):
        '''Clears core and gtkUi, and fixes button to next step.'''
        # cleanup
        self.nb.set_current_page(0)
        self.w3af.cleanup()
        messages.getQueueDiverter(reset=True)
        self.setTabs(False)
        self.sb("Scan results cleared")

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
        self._setTab(sensit, "Results", scanrun.ScanRunBody)
        self._setTab(sensit, "Log",     logtab.LogBody)
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
#        import pdb;pdb.set_trace()
        if page_num == 1:
            page = "Results"
        elif page_num == 3:
            page = "Exploit"
        else:
            page = None

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

    def profileAction(self, action):
        print "action", action
        methname = action + "Profile"
        method = getattr(self.profiles, methname)
        method()

    def activateProfileActions(self, newstatus):
        '''Activate profiles buttons.

        @param newstatus: if the profile changed or not.
        '''
        for opt,stt in zip(self.profileActions, newstatus):
            opt.set_sensitive(stt)
        
def main(profile):
    MainApp(profile)
