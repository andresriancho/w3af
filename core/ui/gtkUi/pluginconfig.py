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
import os
import core.ui.gtkUi.entries as entries
import core.ui.gtkUi.helpers as helpers
from core.controllers.w3afException import w3afException

# support for <2.5
if sys.version_info[:2] < (2,5):
    all = helpers.all
    any = helpers.any

# decision of which widget implements the option to each type
wrapperWidgets = {
    "boolean": entries.BooleanOption,
    "integer": entries.IntegerOption,
    "string": entries.StringOption,
    "float": entries.FloatOption,
    "list": entries.ListOption,
}

class Option(object):
    '''Plugin configuration option.

    @param option: an XML node with the option information

    Received the semiparsed XML from the plugin, and store in self the 
    option attributes (default, desc, help and type).

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, option):
        self.name = option.getAttribute('name')
        for tag in "default desc help type".split():
            try:
                value = option.getElementsByTagName(tag)[0].childNodes[0].data
            except:
                value = ""
            setattr(self, tag, value)

    def __str__(self):
        return "Option %s <%s> [%s] (%s)" % (self.name, self.type, self.default, self.desc)

    def getFullConfig(self):
        '''Collects the configuration of the plugin in a dict.

        @return: A dict with the configuration.
        '''
        d = {}
        for tag in "desc help type".split():
            d[tag] = getattr(self, tag)
        d['default'] = self.widg.getValue()
        return d
        

class EasyTable(gtk.Table):
    '''Simplification of gtk.Table.

    @param arg: all it receives goes to gtk.Table
    @param kw: all it receives goes to gtk.Table

    This class is to have a simple way to add rows to the table.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, *arg, **kw):
        super(EasyTable,self).__init__(*arg, **kw)
        self.auto_rowcounter = 0
        self.set_row_spacings(1)

    def autoAddRow(self, *widgets):
        '''Simple way to add rows to a table.

        @param widgets: all the widgets to the row

        This method creates a new row, adds the widgets and show() them.
        '''
        r = self.auto_rowcounter
        for i,widg in enumerate(widgets):
            if widg is not None:
                self.attach(widg, i, i+1, r, r+1, yoptions=gtk.EXPAND, xpadding=5)
                widg.show()
        self.auto_rowcounter += 1


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
    def __init__(self, plugin_tree, plugin, title, options):
        super(OptionsPanel,self).__init__()
        self.set_spacing(5)
        self.plugin_tree = plugin_tree
        self.options = options
        
        # initial title
        titl = gtk.Label(title)
        titl.set_alignment(0.0, 0.5)
        titl.show()
        self.pack_start(titl)

        # middle table (the heart of the panel)
        tabbox = gtk.HBox()
        table = self._makeTable()
        tabbox.pack_start(table, expand=False)
        tabbox.show()
        self.pack_start(tabbox, expand=True, fill=False)

        # last row buttons
        hbox = gtk.HBox()
        self.save_btn = gtk.Button("Save configuration")
        self.save_btn.set_sensitive(False)
        self.save_btn.connect("clicked", self._savePanel, plugin)
        self.save_btn.show()
        hbox.pack_start(self.save_btn, expand=False, fill=False)
        self.rvrt_btn = gtk.Button("Revert values")
        self.rvrt_btn.set_sensitive(False)
        self.rvrt_btn.connect("clicked", self._revertPanel)
        self.rvrt_btn.show()
        hbox.pack_start(self.rvrt_btn, expand=False, fill=False)
        hbox.show()
        self.pack_end(hbox, expand=False, fill=False)

        self.show()

    def _makeTable(self):
        '''Creates the table in which all the options are shown.

        @return: The created table

        For each row, it will put:

            - the option label
            - the configurable widget (textentry, checkbox, etc.)
            - an optional button to get more help (if the help is available)

        Also, the configurable widget gets a tooltip for a small description.
        '''
        table = EasyTable(len(self.options), 3)
        self.widgets_status = {}
        self.propagAnyWidgetChanged = helpers.PropagateBuffer(self._changedAnyWidget)
        tooltips = gtk.Tooltips()
        for i,opt in enumerate(self.options):
            titl = gtk.Label(opt.name)
            titl.set_alignment(0.0, 0.5)
#            propagWidgetChanged = helpers.PropagateBuffer(self._changedWidget)
            widg = wrapperWidgets[opt.type](self._changedWidget, opt.default)
            opt.widg = widg
            tooltips.set_tip(widg, opt.desc)
            if opt.help:
                helpbtn = entries.SemiStockButton("", gtk.STOCK_INFO)
                cleanhelp = helpers.cleanDescription(opt.help)
                helpbtn.connect("clicked", self._showHelp, cleanhelp)
            else:
                helpbtn = None
            table.autoAddRow(titl, widg, helpbtn)
            self.widgets_status[widg] = (titl, opt.name, "<b>%s</b>" % opt.name)
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
        self.plugin_tree.configChanged(like_initial)

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
                    invalid.append(opt.name)
        if invalid:
            msg = "The configuration can't be saved, there is a problem in the following parameter(s):\n\n"
            msg += "\n".join(invalid)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title('Configuration error')
            dlg.run()
            dlg.destroy()
            return

        # we get the values, save, and if the save is ok, we
        # fix the values in the widgets
        tosave = {}
        for opt in self.options:
            tosave[opt.name] = opt.getFullConfig()
        w3af = self.plugin_tree.w3af
        try:
            helpers.coreWrap(w3af.setPluginOptions, plugin.pname, plugin.ptype, tosave)
        except w3afException:
            return
        for opt in self.options:
            opt.widg.save()

    def _revertPanel(self, *vals):
        '''Revert all widgets to their initial state.'''
        for widg in self.widgets_status:
            widg.revertValue()


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

    def config(self, plugin, xmloptions, longdesc):
        '''Creates and shows the configuration panel.
        
        @param plugin: the plugin to configure
        @param xmloptions: the options in xml
        @param longdesc: the long description of the plugin
        '''
        idplugin = id(plugin)
        try:
            newwidg = self.created_panels[idplugin]
        except KeyError:
            options = []
            xmlDoc = xml.dom.minidom.parseString(xmloptions)
            for xmlOpt in xmlDoc.getElementsByTagName('Option'):
                option = Option(xmlOpt)
                options.append(option)

            if options:
                newwidg = OptionsPanel(self.plugin_tree, plugin, longdesc, options)
            else:
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

    @param scantab: The scantab where the scanok button leaves.
    @param w3af: The main core class.
    @param config_panel: The configuration panel, to handle each plugin config

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, scantab, w3af, config_panel):
        self.scantab = scantab 
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
        
        # button-press-event, to handle right click
        self.connect('button-press-event', self.popup_menu)

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
        self.scantab.scanok.change(self, isallok)

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

    def editPlugin( self, widget, pluginName, pluginType ):
        '''
        I get here when the user right clicks on a plugin name, then he clicks on "Edit..."
        This method calls the plugin editor as a separate process and exists.
        '''
        program = 'python'
        fName = 'plugins/' + pluginType + '/' + pluginName + '.py'
        try:
            os.spawnvpe(os.P_NOWAIT, 'python', ['python','core/ui/gtkUi/pluginEditor.py', fName, ''], os.environ)
        except os.error:
            msg = 'Error while starting the w3af plugin editor.'
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title('Error')
            dlg.run()
            dlg.destroy()
        
    def popup_menu( self, tv, event ):
        '''Shows a menu when you right click on a plugin.
        
        @param tv: the treeview.
        @parameter event: The GTK event 
        '''
        if event.button == 3:
            # It's a right click !
            _x = int(event.x)
            _y = int(event.y)
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
                e.connect('activate', self.editPlugin, pname, ptype )
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
            options = plugin.getOptionsXML()
            longdesc = plugin.getLongDesc()
            longdesc = helpers.cleanDescription(longdesc)
            self.config_panel.config(plugin, options, longdesc)

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
    
    @param scantab: the tab of the main notepad
    @param w3af: the main core class

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, scantab, w3af):
        super(PluginConfigBody,self).__init__()

        # the paned window
        pan = gtk.HPaned()
        a2 = ConfigPanel()
        self.plugin_tree = PluginTree(scantab, w3af, a2)
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

        # target url
        targetbox = gtk.HBox()
        lab = gtk.Label("Target:")
        lab.show()
        targetbox.pack_start(lab, expand=False, fill=False, padding=10)
        self.target = entries.AdvisedEntry("Insert the target URL here", scantab.scanok)
        self.target.connect("activate", scantab._startScan)
        self.target.show()
        targetbox.pack_start(self.target, expand=True, fill=True, padding=10)
        self.pack_start(targetbox, expand=False, fill=False)
        targetbox.show()

        self.show()

    def getActivatedPlugins(self):
        '''Return the activated plugins.

        @return: all the plugins that are active.
        '''
        return self.plugin_tree.getActivatedPlugins()
