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

import core.controllers.w3afCore
import core.controllers.miscSettings
from core.controllers.w3afException import w3afException
import core.ui.gtkUi.scantab as scantab
import core.ui.gtkUi.exploittab as exploittab
import core.ui.gtkUi.httpLogTab as httpLogTab
import core.ui.gtkUi.helpers as helpers
import core.ui.gtkUi.confpanel as confpanel
try:
    import core.ui.gtkUi.mozillaTab as mozillaTab
    withMozillaTab = True
except Exception, e:
    withMozillaTab = False
    

ui_menu = """
<ui>
  <menubar name="MenuBar">
    <menu action="SessionMenu">
      <menuitem action="Save"/>
      <menuitem action="Resume"/>
    </menu>
    <menu action="ViewMenu">
      <menuitem action="KBExplorer"/>
      <menuitem action="LogWindow"/>
      <menuitem action="URLWindow"/>
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
    <toolitem action="Resume"/>
  </toolbar>
</ui>
"""

class ConfigDialog(gtk.Dialog):
    '''Puts a Config panel inside a Dialog.
    
    @param title: the title of the window.
    @param w3af: the Core instance
    @param plugin: the plugin to configure

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title, w3af, plugin):
        super(ConfigDialog,self).__init__(title, None, gtk.DIALOG_MODAL, ())

        # buttons and config panel
        save_btn = self.add_button("Save configuration", 0)
        rvrt_btn = self.add_button("Revert configuration", 0)
        plugin.pname, plugin.ptype = plugin.getName(), plugin.getType()
        panel = confpanel.OnlyOptions(self, w3af, plugin, save_btn, rvrt_btn)
        self.vbox.pack_start(panel)

        self.like_initial = True
        self.connect_after("delete_event", self.close)
        self.show()

    def configChanged(self, like_initial):
        '''Propagates the change from the options.

        @params like_initial: If the config is like the initial one
        '''
        self.like_initial = like_initial

    def close(self, widget, event):
        '''Handles the user trying to close the configuration.

        If the config is not saved, just alert it.
        '''
        if self.like_initial:
            return False

        msg = "Do you want to quit without saving the changes?"
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
        stayhere = dlg.run() != gtk.RESPONSE_YES
        dlg.destroy()
        return stayhere

class MainApp:
    '''Main GTK application

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
        self.window.connect("delete_event", self.quit)
        self.window.set_title("w3af - Web Application Attack and Audit Framework")
#        self.window.set_border_width(2)
        self.window.resize(800, 600)
        mainvbox = gtk.VBox()
        self.window.add(mainvbox)
        mainvbox.show()

        self.w3af = core.controllers.w3afCore.w3afCore()

        # Create a UIManager instance
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')

        # Create actions
        actiongroup.add_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback
            ('Save', gtk.STOCK_SAVE, '_Save session', None, 'Save actual session to continue later', self.notyet),
            ('Resume', gtk.STOCK_OPEN, '_Restore session', None, 'Restore a previously saved session', self.notyet),
            ('SessionMenu', None, '_Session'),
            ('KBExplorer', None, '_KB Explorer', None, 'Toggle the Knowledge Base Explorer', self.notyet),
            ('LogWindow', None, '_Log Window', None, 'Toggle the Log Window', self.notyet),
            ('URLWindow', None, '_URL Window', None, 'Toggle the URL Window', self.notyet),
            ('ViewMenu', None, '_View'),
            ('URLconfig', None, '_URL Config', None, 'URL configuration', self.menu_config_url),
            ('Miscellaneous', None, '_Miscellaneous', None, 'Miscellaneous configuration', self.menu_config_misc),
            ('ConfigurationMenu', None, '_Configuration'),
            ('Help', None, '_Help', None, 'Help regarding the framework', self.notyet),
            ('About', None, '_About', None, 'About the framework', self.notyet),
            ('HelpMenu', None, '_Help'),
        ])

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI description
        uimanager.add_ui_from_string(ui_menu)

        # menubar and toolbar
        menubar = uimanager.get_widget('/MenuBar')
        mainvbox.pack_start(menubar, False)
        toolbar = uimanager.get_widget('/Toolbar')
        mainvbox.pack_start(toolbar, False)

        # notebook
        self.nb = gtk.Notebook()
        mainvbox.pack_start(self.nb, True)
        self.nb.show()

        # scan tab
        scan = scantab.ScanTab(self, self.w3af)
        label = gtk.Label("Scan")
        self.nb.append_page(scan, label)

        # mozilla tab
        if withMozillaTab:
            browser = mozillaTab.mozillaTab(self.w3af)
            label = gtk.Label("Browser")
            self.nb.append_page(browser, label)
        
        # Request Response navigator
        htl = httpLogTab.httpLogTab(self.w3af)
        label = gtk.Label("HTTP Log")
        self.nb.append_page(htl, label)

        # FIXME: missing, put a placeholder
        # third tab
        # FIXME: missing, put a placeholder

        # exploit tab
        self.dummy = gtk.Label("No scan info is gathered yet")
        label = gtk.Label("Exploit")
        label.set_sensitive(False)
        self.dummy.set_sensitive(False)
        self.nb.append_page(self.dummy, label)
        self.dummy.show()

#        # status bar
#        # FIXME implement in a future
#        self._sb = gtk.Statusbar()
#        mainvbox.pack_start(self._sb, False)
#        self._sb_context = self._sb.get_context_id("unique_sb")
#        self._sb.show()
#        self.sb("Program started ok")

        self.window.show()
        helpers.init(self.window)
        gtk.main()

#    def sb(self, text):
#        # FIXME implement in a future
#        self._sb.push(self._sb_context, text)

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

    def activateExploit(self):
        '''Creates the exploit tab.'''
        # create the exploit and label
        self.exploit = exploittab.ExploitBody(self.w3af)
        label = gtk.Label("Exploit")

        # remove old page and insert this one
        pos = self.nb.page_num(self.dummy)
        self.nb.remove_page(pos)
        self.nb.insert_page(self.exploit, label, pos)
        
    def menu_config_url(self, action):
        plugin = self.w3af.uriOpener.settings
        ConfigDialog("Configure URL settings", self.w3af, plugin)

    def menu_config_misc(self, action):
        plugin = core.controllers.miscSettings.miscSettings()
        ConfigDialog("Configure Misc settings", self.w3af, plugin)


def main():
    MainApp()
