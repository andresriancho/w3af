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

import pygtk
pygtk.require('2.0')
import gtk, gobject
import xml.dom, sys

import core.ui.gtkUi.confpanel as confpanel
import core.ui.gtkUi.entries as entries
import core.ui.gtkUi.helpers as helpers
from core.ui.gtkUi.pluginEditor import editPlugin
from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.basePlugin import basePlugin
from core.controllers.misc import parseOptions

# support for <2.5
if sys.version_info[:2] < (2,5):
    all = helpers.all
    any = helpers.any

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
    def __init__(self, plugin_tree, plugin, title):
        super(OptionsPanel,self).__init__()
        self.set_spacing(5)
        self.plugin_tree = plugin_tree
        
        # initial title
        titl = gtk.Label(title)
        titl.set_alignment(0.0, 0.5)
        titl.show()
        self.pack_start(titl)

        # last row buttons
        hbox = gtk.HBox()
        save_btn = gtk.Button("Save configuration")
        save_btn.show()
        hbox.pack_start(save_btn, expand=False, fill=False)
        rvrt_btn = gtk.Button("Revert to previous values")
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

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        super(ConfigPanel,self).__init__(False, 0)
        self.widg = None
        self.clear()
        self.show()
        self.created_panels = {}

    def config(self, plugin, longdesc):
        '''Creates and shows the configuration panel.
        
        @param plugin: the plugin to configure
        @param xmloptions: the options in xml
        @param longdesc: the long description of the plugin
        '''
        idplugin = id(plugin)
        try:
            newwidg = self.created_panels[idplugin]
        except KeyError:
            newwidg = OptionsPanel(self.plugin_tree, plugin, longdesc)
            if not newwidg.options.options:
                newwidg = None
            self.created_panels[idplugin] = newwidg

        if newwidg is None:
            return self.clear(longdesc, "This plugins has no options to configure")

        self.remove(self.widg)
        self.pack_start(newwidg, expand=True)
        self.widg = newwidg

    def clear(self, title=None, label=""):
        '''Shows an almost empty panel when there's no configuration.

        @param title: the title to show in the top (optional)
        @param label: a message to the middle of the panel (optional).

        When it does not receive nothing, the panel is clean.
        '''
        vbox = gtk.VBox()
        vbox.set_spacing(5)

        if title is not None:
            titl = gtk.Label(title)
            titl.set_alignment(0.0, 0.5)
            titl.show()
            vbox.pack_start(titl)

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
    def __init__(self, mainwin, w3af, config_panel):
        self.mainwin = mainwin 
        self.w3af = w3af
        self.config_panel = config_panel

        # create the TreeStore, with the following columns:
        # 1. the plugin name, to show it
        # 2. checkbox status, active or not
        # 3. checkbox status, inconsistant or not
        # 4. the plugin name, just to store and bold it or not
        self.treestore = gtk.TreeStore(str, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN, str)

        # just build the tree with the plugin names
        # gtkOutput plugin is enabled at start
        for plugintype in sorted(w3af.getPluginTypes()):
            incons = int(plugintype == "output")
            father = self.treestore.append(None, [plugintype, 0, incons, plugintype])
            for plugin in sorted(w3af.getPluginList(plugintype)):
                activ = int(plugin == "gtkOutput")
                self.treestore.append(father, [plugin, activ, 0, plugin])

        # we will not ask for the plugin instances until needed, we'll
        # keep them here:
        self.plugin_instances = {}

        # we'll supervise the status of all changed configurations (if it
        # does not exist here, never was changed)
        self.config_status = {}

        # create the TreeView using treestore
        super(PluginTree,self).__init__(self.treestore)
        self.connect('cursor-changed', self.configure_plugin)
        
        # button-release-event, to handle right click
        self.connect('button-release-event', self.popup_menu)

        # create a TreeViewColumn for the text
        tvcolumn = gtk.TreeViewColumn('Plugin')
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'markup', 0)
        self.append_column(tvcolumn)

        # create a TreeViewColumn for the checkbox
        tvcolumn = gtk.TreeViewColumn('Active')
        cell = gtk.CellRendererToggle()
        cell.set_property('activatable', True)
        cell.connect('toggled', self.activatePlugin)
        tvcolumn.pack_start(cell, False)
        tvcolumn.add_attribute(cell, 'active', 1)
        tvcolumn.add_attribute(cell, 'inconsistent', 2)
        self.append_column(tvcolumn)

        #self.set_enable_tree_lines(True)

        self.show()

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
        plugin = self.w3af.getPluginInstance(pname, ptype)
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
            if path != None and len(path) > 1:
                # Get the information about the click
                pname = self.treestore[path][3]
                ptype = self.treestore[path[:1]][3]
                
                # Ok, now I show the popup menu !
                # Create the popup menu
                gm = gtk.Menu()
                
                # And the items
                e = gtk.MenuItem("Edit plugin...")
                e.connect('activate', editPlugin, pname, ptype )
                gm.append( e )
                gm.show_all()
                
                gm.popup( None, None, None, event.button, _time)
        
    def configure_plugin(self, tv):
        '''Starts the plugin configuration.

        @param tv: the treeview.
        '''
        (path, column) = tv.get_cursor()
        if path is None:
            return

        if len(path) == 1:
            pluginType = self.treestore[path][3]
            self.w3af.getPluginTypesDesc( pluginType )
            label = helpers.cleanDescription( self.w3af.getPluginTypesDesc( pluginType ) )
            self.config_panel.clear(label=label )
        else:
            plugin = self._getPluginInstance(path)
            longdesc = plugin.getLongDesc()
            longdesc = helpers.cleanDescription(longdesc)
            self.config_panel.config(plugin, longdesc)

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
        if treerow[0] == "gtkOutput":
            return

        # invert the active state and make it consistant
        newvalue = not treerow[1]
        treerow[1] = newvalue
        treerow[2] = False

        # path can be "?" if it's a father or "?:?" if it's a child
        if ":" not in path:
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
            # child: let's change the father status
            vals = []
            pathfather = path.split(":")[0]
            father = self.treestore[pathfather]
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

    def getActivatedPlugins(self):
        '''Return the activated plugins.

        @return: all the plugins that are active.
        '''
        result = []
        for row in self.treestore:
            plugins = []
            type = row[3]
            for childrow in self._getChildren(row.path):
                plugin = childrow[3]
                if childrow[1]:
                    plugins.append(plugin)
            if plugins:
                result.append((type, plugins))
        return result



class PluginConfigBody(gtk.VBox):
    '''The main Plugin Configuration Body.
    
    @param mainwin: the tab of the main notepad
    @param w3af: the main core class

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, mainwin, w3af):
        super(PluginConfigBody,self).__init__()
        self.w3af = w3af

        # target url
        targetbox = gtk.HBox()
        lab = gtk.Label("Target:")
        lab.show()
        targetbox.pack_start(lab, expand=False, fill=False, padding=5)
        self.target = entries.AdvisedEntry("Insert the target URL here", mainwin.scanok.change)
        self.target.connect("activate", mainwin._scan_director)
        self.target.show()
        targetbox.pack_start(self.target, expand=True, fill=True, padding=5)
        advbut = entries.SemiStockButton("", gtk.STOCK_PREFERENCES, "Advanced Target URL configuration")
        advbut.connect("clicked", self._advancedTarget)
        advbut.show()
        targetbox.pack_start(advbut, expand=False, fill=False, padding=5)
        targetbox.show()
        self.pack_start(targetbox, expand=False, fill=False)

        # the paned window
        pan = gtk.HPaned()
        a2 = ConfigPanel()
        self.plugin_tree = PluginTree(mainwin, w3af, a2)
        a2.plugin_tree = self.plugin_tree
        
        # left
        scrollwin1 = gtk.ScrolledWindow()
        scrollwin1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin1.add_with_viewport(self.plugin_tree)
        scrollwin1.show()

        # rigth
        scrollwin2 = gtk.ScrolledWindow()
        scrollwin2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin2.add_with_viewport(a2)
        scrollwin2.show()

        # pack it all and show
        pan.pack1(scrollwin1)
        pan.pack2(scrollwin2)
        pan.set_position(250)
        pan.show()
        self.pack_start(pan, padding=5)

        self.show()

    def _advancedTarget(self, widg):
        # overwrite the plugin info with the target url
        plugin = self.w3af.target
        options = parseOptions.parseXML(plugin.getOptionsXML())
        url = self.target.get_text()

        # open config
        confpanel.ConfigDialog("Advanced target settings", self.w3af, plugin, {"target":url})

        # update the Entry with plugin info
        options = parseOptions.parseXML(plugin.getOptionsXML())
        self.target.set_text(options['target']['default'])

    def getActivatedPlugins(self):
        '''Return the activated plugins.

        @return: all the plugins that are active.
        '''
        return self.plugin_tree.getActivatedPlugins()
