'''
confpanel.py

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
from . import entries, helpers
from core.controllers.w3afException import w3afException

from core.controllers.basePlugin.basePlugin import basePlugin
from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin

from core.data.options.optionList import optionList
import core.controllers.outputManager as om

class OnlyOptions(gtk.VBox):
    '''Only the options for configuration.

    @param parentwidg: The parentwidg, to propagate changes
    @param plugin: The selected plugin, for which the configuration is.
    @param options: The options to configure.
    @param save_btn: The save button.
    @param rvrt_btn: The revert button.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, parentwidg, w3af, plugin, save_btn, rvrt_btn, overwriter=None):
        super(OnlyOptions,self).__init__()
        if overwriter is None:
            overwriter = {}
        self.set_spacing(5)
        self.w3af = w3af
        self.parentwidg = parentwidg
        self.widgets_status = {}
        self.tab_widget = {}
        self.propagAnyWidgetChanged = helpers.PropagateBuffer(self._changedAnyWidget)
        self.propagLabels = {}

        # options
        self.options = optionList()
        options = plugin.getOptions()
        # let's use the info from the core
        coreopts = self.w3af.plugins.getPluginOptions(plugin.ptype, plugin.pname)
        if coreopts is None:
            coreopts = {}

        # let's get the real info
        for opt in options:
            if opt.getName() in coreopts:
                opt.setValue( coreopts[opt.getName()].getValueStr() )
            if opt.getName() in overwriter:
                opt.setValue( overwriter[opt.getName()] )
            self.options.append(opt)

        # buttons
        save_btn.connect("clicked", self._savePanel, plugin)
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
        self.parentwidg.configChanged(like_initial)

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

    def _savePanel(self, widg, plugin):
        '''Saves the config changes to the plugins.

        @param widg: the widget who generated the signal
        @param plugin: the plugin to save the configuration

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
        
        try:
            # Get the value from the GTK widget and set it to the option object
            for opt in self.options:
                helpers.coreWrap(opt.setValue, opt.widg.getValue())

            if isinstance(plugin, basePlugin):
                helpers.coreWrap(self.w3af.plugins.setPluginOptions, plugin.ptype, plugin.pname, self.options)
            else:
                helpers.coreWrap(plugin.setOptions, self.options)
        except w3afException:
            return
        for opt in self.options:
            opt.widg.save()
            
        # Tell the profile tree that something changed
        self.w3af.mainwin.profiles.profileChanged(changed=True)
        
        # Status bar
        self.w3af.mainwin.sb("Plugin configuration saved successfully")

    def _revertPanel(self, *vals):
        '''Revert all widgets to their initial state.'''
        for widg in self.widgets_status:
            widg.revertValue()
        self.w3af.mainwin.sb("The plugin configuration was reverted to its last saved state")


class ConfigDialog(gtk.Dialog):
    '''Puts a Config panel inside a Dialog.
    
    @param title: the title of the window.
    @param w3af: the Core instance
    @param plugin: the plugin to configure
    @param overwriter: a dict of pair (config, value) to overwrite the plugin
                       actual value

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, title, w3af, plugin, overwriter=None, showDesc=False):
        super(ConfigDialog,self).__init__(title, None, gtk.DIALOG_MODAL, ())
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        if overwriter is None:
            overwriter = {}

        # buttons and config panel
        save_btn = self._button("Save configuration")
        rvrt_btn = self._button("Revert to previous configuration")
        close_btn = self._button(stock=gtk.STOCK_CLOSE)
        close_btn.connect("clicked", self._btn_close)
        plugin.pname, plugin.ptype = plugin.getName(), plugin.getType()
        
        # Show the description
        if showDesc:
            # The long description of the plugin
            longLabel = gtk.Label()
            longLabel.set_text( plugin.getLongDesc() )
            longLabel.set_alignment(0.0, 0.5)
            longLabel.show()
            self.vbox.pack_start(longLabel)
        
        # Save it , I need it when I inherit from this class
        self._plugin = plugin
        self._panel = OnlyOptions(self, w3af, plugin, save_btn, rvrt_btn, overwriter)
        self.vbox.pack_start(self._panel)

        self.like_initial = True
        self.connect("event", self._evt_close)
        self.run()
        self.destroy()

    def _button(self, text="", stock=None):
        '''Creates a button.'''
        b = gtk.Button(text, stock)
        b.show()
        self.action_area.pack_start(b)
        return b

    def configChanged(self, like_initial):
        '''Propagates the change from the options.

        @params like_initial: If the config is like the initial one
        '''
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

class AdvancedTargetConfigDialog(ConfigDialog):
    '''Inherits from the config dialog and overwrites the close method
    
    @param title: the title of the window.
    @param w3af: the Core instance
    @param plugin: the plugin to configure
    @param overwriter: a dict of pair (config, value) to overwrite the plugin
                       actual value

    @author: Andres Riancho
    '''
    def __init__(self, title, w3af, plugin, overwriter=None):
        if overwriter is None:
            overwriter = {}
        ConfigDialog.__init__(self, title, w3af, plugin, overwriter)
        
    def _close(self):
        '''Advanced target close that makes more sense.'''
        if self.like_initial:
            return False

        msg = "Do you want to save the configuration?"
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
        saveConfig = dlg.run() == gtk.RESPONSE_YES
        dlg.destroy()
        
        if saveConfig:
            self._panel._savePanel( self._panel, self._plugin )
            
        return False
    
