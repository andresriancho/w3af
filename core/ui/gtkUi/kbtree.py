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
import core.data.kb

TYPES_OBJ = {
    core.data.kb.vuln.vuln: "vuln",
    core.data.kb.info.info: "info",
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
    def __init__(self, filter, title, strict):
        self.strict = strict

        # simple empty Tree Store
        # columns: the string to show; the key for the plugin instance
        self.treestore = gtk.TreeStore(str, str)
        gtk.TreeView.__init__(self, self.treestore)
        #self.set_enable_tree_lines(True)

        # the TreeView column
        tvcolumn = gtk.TreeViewColumn(title)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, "text", 0)
        self.append_column(tvcolumn)

        # this tree structure will keep the parents where to insert nodes
        self.treeholder = {}

        # here we will hold the instances, the key will be stored in the store
        self.instances = {}

        # initial filters
        self.filter = filter

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
                holdvariab = {}

                # iterate the third layer, the variable objects
                if isinstance(variabobjects, list):
                    for obj in variabobjects:
                        idobject = str(obj)
                        if idobject not in holdvariab:
                            type_obj = TYPES_OBJ.get(type(obj), "misc")
                            # the type must be in the filter, and be in True
                            if self.filter.get(type_obj,False): 
                                holdvariab[idobject] = obj
                else:
                    # Not a list, try to show it anyway
                    # This is an ugly hack, because these structures in the core
                    # are not as clean as should be
                    # Use this strict parameter to decide if you will show as much
                    # as possible, or want to be strict regarding the type here
                    if not self.strict:
                        idobject = self._getBestObjName(variabobjects)
                        if idobject not in holdvariab and self.filter["misc"]:
                            holdvariab[idobject] = None

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
        new_treestore = gtk.TreeStore(str, str)
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
                treeplugin = treestore.append(None, [pluginname, 0])
                holdplugin = {}
                treeholder[pluginname] = (treeplugin, holdplugin)

            # iterate the second layer, variable names
            for variabname, variabobjects in plugvalues.iteritems():
                if variabname in holdplugin:
                    (treevariab, holdvariab) = holdplugin[variabname]
                else:
                    treevariab = treestore.append(treeplugin, [variabname, 0])
                    holdvariab = set()
                    holdplugin[variabname] = (treevariab, holdvariab)

                # iterate the third layer, the variable objects
                for name,instance in variabobjects.items():
                    if name not in holdvariab:
                        holdvariab.add(name)
                        idinstance = str(id(instance))
                        treestore.append(treevariab, [name, idinstance])
                        self.instances[idinstance] = instance

        return True
                        
