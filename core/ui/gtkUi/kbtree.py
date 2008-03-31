'''
kbtree.py

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

import core.data.kb.knowledgeBase as kb
import core.ui.gtkUi.helpers as helpers
import core.data.kb

TYPES_OBJ = {
    core.data.kb.vuln.vuln: "vuln",
    core.data.kb.info.info: "info",
}

OBJ_ICONS = {
    "vuln": helpers.loadPixbuf('core/ui/gtkUi/data/vulnerability.png'),
    "info": helpers.loadPixbuf('core/ui/gtkUi/data/information.png'),
}


class KBTree(gtk.TreeView):
    '''Show the Knowledge Base in a tree.
    
    @param filter: the initial filter
    @param title: the title to show
    @param strict: if the tree will show exactly what is filtered

    Regarding the strict parameter: as these structures are not as clean as 
    they should in the Core, some information does not have a way to be
    determined if they fall in or out of the filter. So, with this parameter
    you control if to show them (strict=False) or not.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, filter, title, strict):
        self.strict = strict
        self.w3af = w3af

        # simple empty Tree Store
        # columns: the string to show; the key for the plugin instance, and the icon
        self.treestore = gtk.TreeStore(str, str, gtk.gdk.Pixbuf)
        gtk.TreeView.__init__(self, self.treestore)
        #self.set_enable_tree_lines(True)

        # the text & icon column
        tvcolumn = gtk.TreeViewColumn(title)
        cell = gtk.CellRendererPixbuf()
        tvcolumn.pack_start(cell, expand=False)
        tvcolumn.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, expand=True)
        tvcolumn.add_attribute(cell, "text", 0)
        self.append_column(tvcolumn)

        # this tree structure will keep the parents where to insert nodes
        self.treeholder = {}

        # here we will hold the instances, the key will be stored in the store
        self.instances = {}

        # initial filters
        self.filter = filter

        # button-release-event, to handle right click
        self.connect('button-release-event', self._popup)

        # get the knowledge base and go live
        self.fullkb = kb.kb.dump()
        gobject.timeout_add(500, self._updateTree, self.treestore, self.treeholder)
        self.show()

    def _filterKB(self):
        '''Calculates the difference between the KB and the tree.

        This way, only is added to the tree those nodes that are new.

        @return: The filtered KB.
        '''
        # let's filter the real kb, to see what we should add
        filteredkb = {}

        # iterate the first layer, plugin names
        for pluginname, plugvalues in self.fullkb.iteritems():
            holdplugin = {}
            
            # iterate the second layer, variable names
            for variabname, variabobjects in plugvalues.iteritems():
                holdvariab = []

                # iterate the third layer, the variable objects
                if isinstance(variabobjects, list):
                    for obj in variabobjects:
                        idobject = self._getBestObjName(obj)
                        type_obj = TYPES_OBJ.get(type(obj), "misc")
                        # the type must be in the filter, and be in True
                        if self.filter.get(type_obj,False): 
                            holdvariab.append((idobject, obj, type_obj))
                else:
                    # Not a list, try to show it anyway
                    # This is an ugly hack, because these structures in the core
                    # are not as clean as should be
                    # Use this strict parameter to decide if you will show as much
                    # as possible, or want to be strict regarding the type here
                    if not self.strict:
                        idobject = self._getBestObjName(variabobjects)
                        if self.filter["misc"]:
                            holdvariab.append((idobject, variabobjects, "misc"))

                if holdvariab:
                    holdplugin[variabname] = holdvariab
            if holdplugin:
                filteredkb[pluginname] = holdplugin
        return filteredkb

    def setFilter(self, active):
        '''Sets a new filter and update the tree.

        @param active: which types should be shown.
        '''
        self.filter = active
        new_treestore = gtk.TreeStore(str, str, gtk.gdk.Pixbuf)
        new_treeholder = {}
        self._updateTree(new_treestore, new_treeholder)
        self.set_model(new_treestore)
        self.treestore = new_treestore
        self.treeholder = new_treeholder

    def _getBestObjName(self,  obj):
        '''
        @return: The best obj name possible
        '''

        if hasattr(obj, "getName"):
            name = obj.getName()
        else:
            name = repr(obj)
        return name
        
    def _updateTree(self, treestore, treeholder):
        '''Updates the GUI with the KB.

        @param treestore: the gui tree to updated.
        @param treeholder: a helping structure to calculate the diff.

        @return: True to keep being called by gobject.
        '''
        filteredKB = self._filterKB()

        # iterate the first layer, plugin names
        for pluginname, plugvalues in filteredKB.iteritems():
            if pluginname in treeholder:
                (treeplugin, holdplugin) = treeholder[pluginname]
            else:
                treeplugin = treestore.append(None, [pluginname, 0, None])
                holdplugin = {}
                treeholder[pluginname] = (treeplugin, holdplugin)

            # iterate the second layer, variable names
            for variabname, variabobjects in plugvalues.iteritems():
                if variabname in holdplugin:
                    (treevariab, holdvariab) = holdplugin[variabname]
                else:
                    treevariab = treestore.append(treeplugin, [variabname, 0, None])
                    holdvariab = set()
                    holdplugin[variabname] = (treevariab, holdvariab)

                # iterate the third layer, the variable objects
                for name,instance,obtype in variabobjects:
                    idinstance = str(id(instance))
                    if idinstance not in holdvariab:
                        holdvariab.add(idinstance)
                        icon = OBJ_ICONS.get(obtype)
                        treestore.append(treevariab, [name, idinstance, icon])
                        self.instances[idinstance] = instance

        return True
                        
    def _popup(self, tv, event):
        '''Shows a menu when you right click on an object inside the kb.
        
        @param tv: the treeview.
        @parameter event: The GTK event 
        '''
        if event.button != 3:
            return

        # is it over a vulnerability?
        (path, column) = tv.get_cursor()
        if path is None:
            return

        # pop up menu
        # I'm leaving this commented because I know that in the future I'll want to
        # do something similar. The code that is commented here, pop-ups a menu
        '''
        menu = gtk.Menu()
        opc = gtk.MenuItem("Show HTTP request and response")
        menu.append(opc)
        menu.popup(None, None, None, event.button, event.time)

        # get instance
        vuln = self.getInstance(path)
        if isinstance(vuln, core.data.kb.vuln.vuln):
            vulnid = vuln.getId()
        
            def goLog(w):
                self.w3af.mainwin.httplog.showReqResById(vulnid)
                self.w3af.mainwin.nb.set_current_page(4)
            opc.connect('activate', goLog)
        else:
            opc.set_sensitive(False)

        menu.show_all()
        '''

    def getInstance(self, path):
        '''Extracts the instance from the tree.

        @param path: where the user is in the tree
        @return The instance
        '''
        instanckey = self.treestore[path][1]
        instance = self.instances.get(instanckey)
        return instance


