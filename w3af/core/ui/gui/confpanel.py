"""
confpanel.py

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

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.data.options.option_list import OptionList
from w3af.core.ui.gui.constants import W3AF_ICON
from w3af.core.ui.gui import entries, helpers


class OnlyOptions(gtk.VBox):
    """Only the options for configuration.

    :param parentwidg: The parentwidg, to propagate changes
    :param plugin: The selected plugin, for which the configuration is.
    :param options: The options to configure.
    :param save_btn: The save button.
    :param rvrt_btn: The revert button.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, parentwidg, w3af, plugin, save_btn, rvrt_btn, overwriter=None):
        super(OnlyOptions, self).__init__()
        if overwriter is None:
            overwriter = {}
        self.set_spacing(5)
        self.w3af = w3af
        self.parentwidg = parentwidg
        self.widgets_status = {}
        self.tab_widget = {}
        self.propagAnyWidgetChanged = helpers.PropagateBuffer(
            self._changedAnyWidget)
        self.propagLabels = {}
        self.saved_successfully = False
        
        # options
        self.options = OptionList()
        options = plugin.get_options()
        # let's use the info from the core
        coreopts = self.w3af.plugins.get_plugin_options(
            plugin.ptype, plugin.pname)
        if coreopts is None:
            coreopts = {}

        # let's get the real info
        for opt in options:
            if opt.get_name() in coreopts:
                opt.set_value(coreopts[opt.get_name()].get_value_str())
            if opt.get_name() in overwriter:
                opt.set_value(overwriter[opt.get_name()])
            self.options.append(opt)

        # buttons
        save_btn.connect("clicked", self._save_panel, plugin)
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

        :return: The created notebook if more than one grouping
        """
        # let's get the tabs, but in order!
        tabs = []
        for o in self.options:
            t = o.get_tabid()
            if t not in tabs:
                tabs.append(t)

        # see if we have more than a tab to create a nb
        if len(tabs) < 2:
            table = self._makeTable(self.options, None)
            return table

        # the notebook
        nb = gtk.Notebook()
        for tab in tabs:
            options = [x for x in self.options if x.get_tabid() == tab]
            if not tab:
                tab = "General"
            label = gtk.Label(tab)
            prop = helpers.PropagateBufferPayload(self._changedLabelNotebook,
                                                  label, tab)
            table = self._makeTable(options, prop)
            nb.append_page(table, label)
        nb.show()
        return nb

    def _makeTable(self, options, prop):
        """Creates the table in which the options are shown.

        :param options: The options to show
        :param prop: The propagation function for this options
        :return: The created table

        For each row, it will put:

            - the option label
            - the configurable widget (textentry, checkbox, etc.)
            - an optional button to get more help (if the help is available)

        Also, the configurable widget gets a tooltip for a small description.
        """
        table = entries.EasyTable(len(options), 3)

        for _, opt in enumerate(options):
            titl = gtk.Label(opt.get_name())
            titl.set_alignment(0.0, 0.5)
            input_widget_klass = entries.wrapperWidgets.get(opt.get_type(),
                                                            entries.TextInput)
            widg = input_widget_klass(self._changedWidget, opt)
            opt.widg = widg
            widg.set_tooltip_text(opt.get_desc())
            if opt.get_help():
                helpbtn = entries.SemiStockButton("", gtk.STOCK_INFO)
                cleanhelp = helpers.clean_description(opt.get_help())
                helpbtn.connect("clicked", self._showHelp, cleanhelp)
            else:
                helpbtn = None
            table.auto_add_row(titl, widg, helpbtn)
            self.widgets_status[widg] = (titl, opt.get_name(),
                                         "<b>%s</b>" % opt.get_name())
            self.propagLabels[widg] = prop
        table.show()
        return table

    def _changedAnyWidget(self, like_initial):
        """Adjust the save/revert buttons and alert the tree of the change.

        :param like_initial: if the widgets are modified or not.

        It only will be called if any widget changed its state, through
        a propagation buffer.
        """
        self.save_btn.set_sensitive(not like_initial)
        self.rvrt_btn.set_sensitive(not like_initial)
        self.parentwidg.config_changed(like_initial)
        self.saved_successfully = False

    def _changedLabelNotebook(self, like_initial, label, text):
        if like_initial:
            label.set_text(text)
        else:
            label.set_markup("<b>%s</b>" % text)

    def _changedWidget(self, widg, like_initial):
        """Receives signal when a widget changed or not.

        :param widg: the widget who changed.
        :param like_initial: if it's modified or not

        Handles the boldness of the option label and then propagates
        the change.
        """
        labl, orig, chng = self.widgets_status[widg]
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

        :param widg: the widget who generated the signal
        :param helpmsg: the message to show in the dialog
        """
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
                                gtk.BUTTONS_OK, helpmsg)
        dlg.set_title('Configuration help')
        dlg.run()
        dlg.destroy()

    def _save_panel(self, widg, plugin):
        """Saves the config changes to the plugins.

        :param widg: the widget who generated the signal
        :param plugin: the plugin to save the configuration

        First it checks if there's some invalid configuration, then gets the
        value of each option and save them to the plugin.
        """
        # check if all widgets are valid
        invalid = []
        for opt in self.options:
            if hasattr(opt.widg, "is_valid"):
                if not opt.widg.is_valid():
                    invalid.append(opt.get_name())
        
        if invalid:
            msg = "The configuration can't be saved, there is a problem in the"\
                  " following parameter(s):\n\n"
            msg += "\n-".join(invalid)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
                                    gtk.BUTTONS_OK, msg)
            dlg.set_title('Configuration error')
            dlg.run()
            dlg.destroy()
            return

        try:
            # Get the value from the GTK widget and set it to the option object
            for opt in self.options:
                SetOptionsWrapper(opt.set_value, opt.widg.get_value())

            if isinstance(plugin, Plugin):
                SetOptionsWrapper(self.w3af.plugins.set_plugin_options,
                                  plugin.ptype, plugin.pname, self.options)
            else:
                SetOptionsWrapper(plugin.set_options, self.options)
        except (BaseFrameworkException, ValueError):
            return
        
        for opt in self.options:
            opt.widg.save()

        # Tell the profile tree that something changed
        self.w3af.mainwin.profiles.profile_changed(changed=True)

        # Status bar
        self.w3af.mainwin.sb("Configuration saved successfully")
        self.saved_successfully = True

    def _revertPanel(self, *vals):
        """Revert all widgets to their initial state."""
        for widg in self.widgets_status:
            widg.revert_value()

        msg = "The plugin configuration was reverted to its last saved state"
        self.w3af.mainwin.sb(msg)

SetOptionsWrapper = helpers._Wrapper((BaseFrameworkException, ValueError))


class ConfigDialog(gtk.Dialog):
    """Puts a Config panel inside a Dialog.

    :param title: the title of the window.
    :param w3af: the Core instance
    :param plugin: the plugin to configure
    :param overwriter: a dict of pair (config, value) to overwrite the plugin
                       actual value

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, title, w3af, plugin, overwriter=None, showDesc=False):
        super(ConfigDialog, self).__init__(title, None, gtk.DIALOG_MODAL, ())
        self.set_icon_from_file(W3AF_ICON)
        if overwriter is None:
            overwriter = {}

        # buttons and config panel
        save_btn = self._button(_("Save configuration"), gtk.STOCK_SAVE)
        rvrt_btn = self._button(_("Revert"),
                                gtk.STOCK_REVERT_TO_SAVED)
        close_btn = self._button(_('Close'), stock=gtk.STOCK_CLOSE)
        close_btn.connect("clicked", self._btn_close)
        plugin.pname, plugin.ptype = plugin.get_name(), plugin.get_type()

        # Show the description
        if showDesc:
            # The long description of the plugin
            long_label = gtk.Label()
            long_label.set_text(plugin.get_long_desc())
            long_label.set_alignment(0.0, 0.5)
            long_label.show()
            self.vbox.pack_start(long_label)

        # Save it , I need it when I inherit from this class
        self._plugin = plugin
        self._panel = OnlyOptions(self, w3af, plugin, save_btn,
                                  rvrt_btn, overwriter)
        self.vbox.pack_start(self._panel)

        self.like_initial = True
        self.connect("event", self._evt_close)
        self.run()
        self.destroy()

    def _button(self, text="", stock=None, tooltip=''):
        """Creates a button."""
        b = entries.SemiStockButton(text, stock, tooltip)
        b.show()
        self.action_area.pack_start(b)
        return b

    def config_changed(self, like_initial):
        """Propagates the change from the options.

        :param like_initial: If the config is like the initial one
        """
        self.like_initial = like_initial

    def _evt_close(self, widget, event):
        """Handles the user trying to close the configuration.

        Filters by event.
        """
        if event.type != gtk.gdk.DELETE:
            return False
        return self._close()

    def _btn_close(self, widget):
        """Handles the user trying to close the configuration."""
        if not self._close():
            self.emit("delete_event", gtk.gdk.Event(gtk.gdk.DELETE))

    def _close(self):
        """Generic close."""
        if self.like_initial:
            return False

        msg = "Do you want to quit without saving the changes?"
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
                                gtk.BUTTONS_YES_NO, msg)
        stayhere = dlg.run() != gtk.RESPONSE_YES
        dlg.destroy()
        return stayhere


class AdvancedTargetConfigDialog(ConfigDialog):
    """Inherits from the config dialog and overwrites the close method

    :param title: the title of the window.
    :param w3af: the Core instance
    :param plugin: the plugin to configure
    :param overwriter: a dict of pair (config, value) to overwrite the plugin
                       actual value

    :author: Andres Riancho
    """
    def __init__(self, title, w3af, plugin, overwriter=None):
        if overwriter is None:
            overwriter = {}
        ConfigDialog.__init__(self, title, w3af, plugin, overwriter)

    def _close(self):
        """Advanced target close that makes more sense."""
        if self.like_initial:
            return False

        msg = "Do you want to save the configuration?"
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
                                gtk.BUTTONS_YES_NO, msg)
        saveConfig = dlg.run() == gtk.RESPONSE_YES
        dlg.destroy()

        if saveConfig:
            self._panel._save_panel(self._panel, self._plugin)

        return False
