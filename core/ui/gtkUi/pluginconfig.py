'''
pluginconfig.py

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

import gtk, gobject
import os

from . import confpanel, entries, helpers
from core.ui.gtkUi.pluginEditor import pluginEditor

from core.controllers.misc.homeDir import get_home_dir


class OptionsPanel(gtk.VBox):
    '''Panel with options for configuration.

    @param plugin_tree: The plugin tree where the plugins are chosen.
    @param plugin: The selected plugin, for which the configuration is.
    @param title: The top description of the options panel
    @param options: The options to configure.

    The panel consists mainly of:
        - the long description of the plugin
        - the table with the options to configure
        - save and revert buttons, at the end

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, plugin_tree, plugin, title, longdesc):
        super(OptionsPanel,self).__init__()
        self.set_spacing(5)
        self.plugin_tree = plugin_tree
        
        # initial title
        titl = gtk.Label()
        titl.set_markup( title )
        titl.set_alignment(0.0, 0.5)
        titl.show()
        self.pack_start(titl)
        
        # The long description of the plugin
        longLabel = gtk.Label()
        longLabel.set_text( longdesc )
        longLabel.set_alignment(0.0, 0.5)
        longLabel.show()
        self.pack_start(longLabel)
        

        # last row buttons
        hbox = gtk.HBox()
        save_btn = gtk.Button(_("Save configuration"))
        save_btn.show()
        hbox.pack_start(save_btn, expand=False, fill=False)
        rvrt_btn = gtk.Button(_("Revert to previous values"))
        rvrt_btn.show()
        hbox.pack_start(rvrt_btn, expand=False, fill=False)
        hbox.show()
        self.pack_end(hbox, expand=False, fill=False)

        # middle (the heart of the panel)
        self.options = confpanel.OnlyOptions(self, self.plugin_tree.w3af, plugin, save_btn, rvrt_btn)
        self.pack_start(self.options, expand=True, fill=False)

        self.show()

    def configChanged(self, like_initial):
        '''Propagates the change from the options.

        @params like_initial: If the config is like the initial one
        '''
        self.plugin_tree.configChanged(like_initial)



class ConfigPanel(gtk.VBox):
    '''Configuration panel administrator.

    Handles the creation of each configuration panel for each plugin.

    @param profileDescription: The description of the selected profile, if any

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, profileDescription=None):
        super(ConfigPanel,self).__init__(False, 0)
        
        if profileDescription is not None:
            # put the description
            lab = gtk.Label(profileDescription)
            lab.set_line_wrap(True)
            self.widg = lab
            lab.show()
            self.add(lab)
        else:
            # put image
            img = gtk.image_new_from_file('core/ui/gtkUi/data/w3af_logo.png')
            self.widg = img
            img.show()
            img.set_sensitive(False)
            self.add(img)

        self.show()
        self.created_panels = {}

    def config(self, plugin_tree, plugin, longdesc):
        '''Creates and shows the configuration panel.
        
        @param plugin: the plugin to configure
        @param xmloptions: the options in xml
        @param longdesc: the long description of the plugin
        '''
        # A title with the name of the plugin in bold and with a bigger font
        title = "<b><big>"+plugin.getName()+"</big></b>\n\n"
        
        idplugin = id(plugin)
        try:
            newwidg = self.created_panels[idplugin]
        except KeyError:
            newwidg = OptionsPanel(plugin_tree, plugin, title, longdesc)
            if not newwidg.options.options:
                newwidg = None
            self.created_panels[idplugin] = newwidg

        if newwidg is None:
            return self.clear(title, longdesc, _("This plugins has no options to configure"))

        self.remove(self.widg)
        self.pack_start(newwidg, expand=True)
        self.widg = newwidg

    def clear(self, title=None, longdesc='', label=""):
        '''Shows an almost empty panel when there's no configuration.

        @param title: the title to show in the top (optional)
        @param title: the long description for the plugin to show in the top (optional)
        @param label: a message to the middle of the panel (optional).

        When it does not receive nothing, the panel is clean.
        '''
        vbox = gtk.VBox()
        vbox.set_spacing(5)

        if title is not None:
            titl = gtk.Label()
            titl.set_markup(title)
            titl.set_alignment(0.0, 0.5)
            titl.show()
            vbox.pack_start(titl)

        if longdesc is not None:
            longLabel = gtk.Label()
            longLabel.set_text(longdesc)
            longLabel.set_alignment(0.0, 0.5)
            longLabel.show()
            vbox.pack_start(longLabel)

        labl = gtk.Label(label)
        labl.show()
        vbox.pack_start(labl)
        
        vbox.show()
        if self.widg is not None:
            self.remove(self.widg)
        self.add(vbox)
        self.widg = vbox


class PluginTree(gtk.TreeView):
    '''A tree showing all the plugins grouped by type.

    @param mainwin: The mainwin where the scanok button leaves.
    @param w3af: The main core class.
    @param config_panel: The configuration panel, to handle each plugin config

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, style, config_panel):
        self.mainwin = w3af.mainwin 
        self.w3af = w3af
        self.config_panel = config_panel

        # create the TreeStore, with the following columns:
        # 1. the plugin name, to show it
        # 2. checkbox status, active or not
        # 3. checkbox status, inconsistant or not
        # 4. the plugin name, just to store and bold it or not
        # 5. a image to show if the plugin is configurable
        self.treestore = gtk.TreeStore(str, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, str, gtk.gdk.Pixbuf)

        # decide which type in function of style
        if style == "standard":
            plugins_toshow = sorted(x for x in w3af.plugins.getPluginTypes() if x != "output")
            col_title = _("Plugin")
        elif style == "output":
            plugins_toshow = ("output",)
            col_title = _("Plugin")
        else:
            raise ValueError("Invalid PluginTree style: %r" % style)

        # just build the tree with the plugin names
        # gtkOutput plugin is enabled at start
        for plugintype in plugins_toshow:

            # let's see if some of the children are activated or not
            pluginlist = w3af.plugins.getPluginList(plugintype)
            activated = set(w3af.plugins.getEnabledPlugins(plugintype))
            if plugintype == "output":
                activated.add("gtkOutput")
            if not activated:
                activ = 0
                incons = 0
            elif len(activated) == len(pluginlist):
                activ = 1
                incons = 0
            else:
                activ = 0
                incons = 1
            father = self.treestore.append(None, [plugintype, activ, incons, plugintype, None])

            dlg = gtk.Dialog()
            editpixbuf = dlg.render_icon(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU)
            for plugin in sorted(w3af.plugins.getPluginList(plugintype)):
                activ = int(plugin in activated)
                if self._getEditablePlugin(plugin, plugintype):
                    thispixbuf = editpixbuf
                else:
                    thispixbuf = None
                self.treestore.append(father, [plugin, activ, 0, plugin, thispixbuf])

        # we will not ask for the plugin instances until needed, we'll
        # keep them here:
        self.plugin_instances = {}

        # we'll supervise the status of all changed configurations (if it
        # does not exist here, never was changed)
        self.config_status = {}

        # create the TreeView using treestore
        super(PluginTree,self).__init__(self.treestore)
        self.connect('cursor-changed', self.configure_plugin)
        
        # button events
        self.connect('button-release-event', self.popup_menu)
        self.connect('button-press-event', self._doubleClick)

        # create a TreeViewColumn for the text and icon
        tvcolumn = gtk.TreeViewColumn(col_title)
        cell = gtk.CellRendererPixbuf()
        tvcolumn.pack_start(cell, expand=False)
        tvcolumn.add_attribute(cell, "pixbuf", 4)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'markup', 0)
        self.append_column(tvcolumn)

        # create a TreeViewColumn for the checkbox
        tvcolumn = gtk.TreeViewColumn(_('Active'))
        cell = gtk.CellRendererToggle()
        cell.set_property('activatable', True)
        cell.connect('toggled', self.activatePlugin)
        tvcolumn.pack_start(cell, False)
        tvcolumn.add_attribute(cell, 'active', 1)
        tvcolumn.add_attribute(cell, 'inconsistent', 2)
        self.append_column(tvcolumn)

        self.show()

    def _doubleClick(self, widg, event):
        '''If double click, expand/collapse the row.'''
        if event.type == gtk.gdk._2BUTTON_PRESS:
            path = self.get_cursor()[0]
            if self.row_expanded(path):
                self.collapse_row(path)
            else:
                self.expand_row(path, False)

    def _getEditablePlugin(self, pname, ptype):
        '''Returns if the plugin has options.'''
        plugin = self.w3af.plugins.getPluginInstance(pname, ptype)
        options = plugin.getOptions()
        return bool(len(options))

    def configChanged(self, like_initial):
        '''Shows in the tree when a plugin configuration changed.

        @param like_initial: if some of the configuration changed
        
        If changed, puts the plugin name in bold. If any of the plugin in a
        type is bold, the type name is also bold.
        '''
        # modify the label of the leaf in the tree
        path = self.get_cursor()[0]
        row = self.treestore[path]
        if like_initial:
            row[0] = row[3]
            # we just alert the changing here, as if it's not saved, the
            # profile shouldn't really be changed
            plugin = self._getPluginInstance(path)
            self.mainwin.profiles.profileChanged(plugin)
        else:
            row[0] = "<b>%s</b>" % row[3]

        # update the general config status, and check if the plugin
        # type has any leaf in changed state
        pathfather = path[0]
        father = self.treestore[pathfather]
        children = self.config_status.setdefault(pathfather, {})
        children[path] = like_initial
        if all(children.values()):
            father[0] = father[3]
        else:
            father[0] = "<b>%s</b>" % father[3]

        # if anything is changed, you can not start scanning
        isallok = all([all(children.values()) for children in self.config_status.values()])
        self.mainwin.scanok.change(self, isallok)

    def _getPluginInstance(self, path):
        '''Caches the plugin instance.

        @param path: where the user is in the plugin tree
        @return The plugin
        '''
        try:
            return self.plugin_instances[path]
        except KeyError:
            pass

        # path can be a tuple of one or two values here
        if len(path) == 1:
            return None

        # here it must use the name in the column 3, as it's always the original
        pname = self.treestore[path][3]
        ptype = self.treestore[path[:1]][3]
        plugin = self.w3af.plugins.getPluginInstance(pname, ptype)
        plugin.pname = pname
        plugin.ptype = ptype
        self.plugin_instances[path] = plugin
        return plugin

    def popup_menu( self, tv, event ):
        '''Shows a menu when you right click on a plugin.
        
        @param tv: the treeview.
        @parameter event: The GTK event 
        '''
        if event.button == 3:
            # It's a right click !
            _time = event.time
            (path, column) = tv.get_cursor()
            # Is it over a plugin name ?
            if path is not None and len(path) > 1:
                # Get the information about the click
                pname = self.treestore[path][3]
                ptype = self.treestore[path[:1]][3]
                
                # Ok, now I show the popup menu !
                # Create the popup menu
                gm = gtk.Menu()
                
                # And the items
                e = gtk.MenuItem(_("Edit plugin..."))
                e.connect('activate', self._handleEditPluginEvent, pname, ptype, path)
                f = gtk.MenuItem(_("Reload plugin"))
                f.connect('activate', self._handleReloadPluginEvent,pname, ptype, path)
                gm.append( e )
                gm.append( f )
                gm.show_all()
                
                gm.popup( None, None, None, event.button, _time)
    
    def _handleReloadPluginEvent(self, widget, pluginName, pluginType, path):
        '''
        I get here when the user right clicks on a plugin name, then he clicks on "Reload plugin"
        This method calls the plugin editor with the corresponding parameters.
        '''
        self._finishedEditingPlugin(path, pluginType, pluginName)
       
    def _handleEditPluginEvent(self, widget, pluginName, pluginType, path):
        '''
        I get here when the user right clicks on a plugin name, then he clicks on "Edit..."
        This method calls the plugin editor with the corresponding parameters.
        '''
        def f(t, n):
            self._finishedEditingPlugin(path, pluginType, pluginName)
        pluginEditor(pluginType,  pluginName,  f)

    def _finishedEditingPlugin(self, path, pluginType, pluginName):
        '''
        This is a callback that is called when the plugin editor finishes.
        '''
        # remove the edited plugin from cache
        del self.plugin_instances[path]
        
        # Reload the plugin
        try:
            self.w3af.plugins.reloadModifiedPlugin(pluginType,  pluginName)
        except Exception, e:
            msg = 'The plugin you modified raised the following exception'
            msg += ' while trying to reload it: "%s",' % str(e)
            msg += ' please fix this issue before continuing or w3af will crash.'
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
            dlg.run()
            dlg.destroy()            
        else:
            # if we still are in the same tree position, refresh the config
            (newpath, column) = self.get_cursor()
            if newpath == path:
                self.configure_plugin()

    def configure_plugin(self, tv=None):
        '''Starts the plugin configuration.

        @param tv: the treeview.
        '''
        (path, column) = self.get_cursor()
        if path is None:
            return

        if len(path) == 1:
            pluginType = self.treestore[path][3]
            desc = self.w3af.plugins.getPluginTypesDesc( pluginType )
            label = helpers.cleanDescription( desc )
            self.config_panel.clear(label=label )
        else:
            plugin = self._getPluginInstance(path)
            longdesc = plugin.getLongDesc()
            longdesc = helpers.cleanDescription(longdesc)
            self.mainwin.profiles.pluginConfig(plugin)
            self.config_panel.config(self, plugin, longdesc)

    def _getChildren(self, path):
        '''Finds the children of a path.

        @param path: the path to find the children.
        @return Yields the childrens.
        '''

        father = self.treestore.get_iter(path)
        howmanychilds = self.treestore.iter_n_children(father)
        for i in range(howmanychilds):
            child = self.treestore.iter_nth_child(father, i)
            treerow = self.treestore[child]
            yield treerow

    def activatePlugin(self, cell, path):
        '''Handles the plugin activation/deactivation.

        @param cell: the cell that generated the signal.
        @param path: the path that clicked the user.

        When a child gets activated/deactivated, the father is also refreshed
        to show if it's full/partially/not activated. 

        If the father gets activated/deactivated, all the children follow the
        same fate.
        '''
        # can not play with this particular plugin
        treerow = self.treestore[path]
        plugin_fam = treerow[0]
        banned_fams = ('discovery', 'evasion')
        
        if plugin_fam == "gtkOutput":
            return

        # invert the active state and make it consistant
        newvalue = not treerow[1]
        treerow[1] = newvalue
        treerow[2] = False
    
        # path can be "?" if it's a father or "?:?" if it's a child
        if ":" not in path:
            # father, lets check if it's the discovery/evasion plugin type
            # if yes, ask for confirmation
            user_response = gtk.RESPONSE_YES
            
            if plugin_fam in banned_fams and treerow[1] == True:
                # The discovery/evasion family is enabled, and the user is
                # disabling it we shouldn't ask this when disabling all the family
                if plugin_fam == 'discovery':
                    msg = _("Enabling all discovery plugins will result in a scan process of several" \
                    " hours, and sometimes days. Are you sure that you want to do enable ALL" \
                    " discovery plugins?")
                else: # evasion family
                    msg = _("Using any of the evasion plugins is highly " \
                            "discouraged in our current version. Are you " \
                            "sure that you want to enable ALL of them?")

                # If the user says NO, then remove the checkbox that was added when the
                # user clicked over the "enable all discovery plugins".
                user_response = self._askUser(msg)
                if user_response != gtk.RESPONSE_YES:
                    treerow[1] = False

            if user_response == gtk.RESPONSE_YES or plugin_fam not in banned_fams:
                # father: let's change the value of all children
                for childtreerow in self._getChildren(path):
                    if childtreerow[0] == "gtkOutput":
                        childtreerow[1] = True
                        if newvalue is False:
                            # we're putting everything in false, except this plugin
                            # so the father is inconsistant
                            treerow[2] = True
                    else:
                        childtreerow[1] = newvalue
        else:
            pathfather = path.split(":")[0]
            father = self.treestore[pathfather]
            plugin_fam = father[0]
            
            if plugin_fam == 'evasion' and treerow[1] == True:
                msg = _("Using any of the evasion plugins is highly " \
                        "discouraged in our current version. Are you sure " \
                        "that you want to enable this plugin?")
                if self._askUser(msg) != gtk.RESPONSE_YES:
                    treerow[1] = False
                
            # child: let's change the father status
            vals = []
            for treerow in self._getChildren(pathfather):
                vals.append(treerow[1])
            if all(vals):
                father[1] = True
                father[2] = False
            elif not any(vals):
                father[1] = False
                father[2] = False
            else:
                father[2] = True

        # alert the profiles that something changed here
        self.mainwin.profiles.profileChanged()

    def getActivatedPlugins(self):
        '''Return the activated plugins.

        @return: all the plugins that are active.
        '''
        result = []
        for row in self.treestore:
            plugins = []
            ptype = row[3]
            for childrow in self._getChildren(row.path):
                plugin = childrow[3]
                if childrow[1]:
                    plugins.append(plugin)
            if plugins:
                result.append((ptype, plugins))
        return result
    
    def _askUser(self, msg):
        '''Displays `msg` on a modal dialog and returns the user's reponse
        '''
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION,
                                gtk.BUTTONS_YES_NO, msg)
        user_response = dlg.run()
        dlg.destroy()
        return user_response
        

class PluginConfigBody(gtk.VBox):
    '''The main Plugin Configuration Body.
    
    @param mainwin: the tab of the main notepad
    @param w3af: the main core class

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, mainwin, w3af):
        super(PluginConfigBody,self).__init__()
        self.w3af = w3af
        targetbox = gtk.HBox()

        # label
        lab = gtk.Label(_("Target:"))
        targetbox.pack_start(lab, expand=False, fill=False, padding=5)

        # entry
        histfile = os.path.join(get_home_dir(),  "urlhistory.pkl")
        self.target = entries.AdvisedEntry(_("Insert the target URL here"), 
                mainwin.scanok.change, histfile, alertmodif=mainwin.profileChanged)
        self.target.connect("activate", mainwin._scan_director)
        self.target.connect("activate", self.target.insertURL)
        targetbox.pack_start(self.target, expand=True, fill=True, padding=5)

        # start/stop button
        startstop = entries.SemiStockButton(_("Start"), gtk.STOCK_MEDIA_PLAY, _("Start scan"))
        startstop.set_sensitive(False)
        startstop.connect("clicked", mainwin._scan_director)
        startstop.connect("clicked", self.target.insertURL)
        mainwin.startstopbtns.addWidget(startstop)
        targetbox.pack_start(startstop, expand=False, fill=False, padding=5)

        # advanced config
        advbut = entries.SemiStockButton("", gtk.STOCK_PREFERENCES, _("Advanced Target URL configuration"))
        advbut.connect("clicked", self._advancedTarget)
        targetbox.pack_start(advbut, expand=False, fill=False, padding=5)
        targetbox.show_all()
        self.pack_start(targetbox, expand=False, fill=False)

        # the pan with all the configs
        self.pan = self._buildpan()
        self.pack_start(self.pan, padding=5)

        # key binding
        self.key_l = gtk.gdk.keyval_from_name("l")
        mainwin.window.connect("key-press-event", self._key)

        self.show()

    def _buildpan(self, profileDescription=None):
        '''Builds the panel.'''
        pan = entries.RememberingHPaned(self.w3af, "pane-plugconfigbody", 250)
        leftpan = entries.RememberingVPaned(self.w3af, "pane-plugconfigleft", 280)
        self.config_panel = ConfigPanel(profileDescription)
        
        # upper left
        scrollwin1u = gtk.ScrolledWindow()
        scrollwin1u.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.std_plugin_tree = PluginTree(self.w3af, "standard", self.config_panel)
        scrollwin1u.add(self.std_plugin_tree)
        scrollwin1u.show()

        # lower left
        scrollwin1l = gtk.ScrolledWindow()
        scrollwin1l.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.out_plugin_tree = PluginTree(self.w3af, "output", self.config_panel)
        scrollwin1l.add(self.out_plugin_tree)
        scrollwin1l.show()

        # pack the left part
        leftpan.pack1(scrollwin1u)
        leftpan.pack2(scrollwin1l)
        leftpan.show()

        # rigth
        scrollwin2 = gtk.ScrolledWindow()
        scrollwin2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin2.add_with_viewport(self.config_panel)
        scrollwin2.show()

        # pack it all and show
        pan.pack1(leftpan)
        pan.pack2(scrollwin2)
        pan.show()
        return pan

    def _advancedTarget(self, widg):
        '''Builds the advanced target widget.'''
        # overwrite the plugin info with the target url
        configurableTarget = self.w3af.target
        options = configurableTarget.getOptions()
        url = self.target.get_text()

        # open config
        confpanel.AdvancedTargetConfigDialog(_("Advanced target settings"), self.w3af, configurableTarget, {"target":url})

        # update the Entry with plugin info
        options = configurableTarget.getOptions()
        self.target.set_text(options['target'].getValueStr())

    def getActivatedPlugins(self):
        '''Return the activated plugins.

        @return: all the plugins that are active.
        '''
        return self.std_plugin_tree.getActivatedPlugins() + self.out_plugin_tree.getActivatedPlugins()

    def editSelectedPlugin(self):
        '''Edits the selected plugin.'''
        treeToUse = None
        if self.out_plugin_tree.is_focus():
            treeToUse = self.out_plugin_tree
        elif self.std_plugin_tree.is_focus():
            treeToUse = self.std_plugin_tree
        else:
            return None

        #self.out_plugin_tree
        (path, column) = treeToUse.get_cursor()
        # Is it over a plugin name ?
        if path is not None and len(path) > 1:
            # Get the information about the click
            pname = treeToUse.treestore[path][3]
            ptype = treeToUse.treestore[path[:1]][3]
            # Launch the editor
            treeToUse._handleEditPluginEvent(None, pname, ptype, path)
        
    def reload(self, profileDescription):
        '''Reloads all the configurations.'''
        # target url
        configurable_obj = self.w3af.target
        options = configurable_obj.getOptions()
        newurl = options['target'].getDefaultValueStr()
        if newurl:
            self.target.setText(newurl)
            self.w3af.mainwin.scanok.change(self.target, True)
        else:
            self.target.reset()
            self.w3af.mainwin.scanok.change(self.target, False)

        # replace panel
        pan = self.get_children()[0]
        newpan = self._buildpan(profileDescription)
        self.remove(self.pan)
        self.pack_start(newpan)
        self.pan = newpan

    def _key(self, widg, event):
        '''Handles keystrokes.'''
        # ctrl-something
        if event.state & gtk.gdk.CONTROL_MASK:
            if event.keyval == self.key_l:   # -l
                self.target.grab_focus()
                return True

        # let the key pass through
        return False
