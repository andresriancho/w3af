'''
scanrun.py

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

import urllib2, time
import core.ui.gtkUi.helpers as helpers
import core.ui.gtkUi.messages as messages
import core.data.kb.knowledgeBase as kb
import core.data.kb

TYPES_OBJ = {
    core.data.kb.vuln.vuln: "vuln",
    core.data.kb.info.info: "info",
}

class KBTree(gtk.TreeView):
    '''Show the Knowledge Base in a tree.
    
    @param kbbrowser: the parent widget
    @param filter: the initial filter

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, kbbrowser, filter):
        self.kbbrowser = kbbrowser

        # simple empty Tree Store
        # first column: the string to show; second column: the long description
        self.treestore = gtk.TreeStore(str, str)
        gtk.TreeView.__init__(self, self.treestore)
        self.connect('cursor-changed', self._showDesc)
        #self.set_enable_tree_lines(True)

        # the TreeView column
        tvcolumn = gtk.TreeViewColumn('Knowledge Base')
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, "text", 0)
        self.append_column(tvcolumn)

        # this tree structure will keep the parents where to insert nodes
        self.treeholder = {}

        # initial filters
        self.filter = filter

        # get the knowledge base and go live
        self.fullkb = kb.kb.dump()
        gobject.timeout_add(500, self._updateTree, self.treestore, self.treeholder)
        self.show()

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

    def _showDesc(self, tv):
        '''Shows the description at the right

        @param tv: the treeview.
        '''
        (path, column) = tv.get_cursor()
        if path is None:
            return
        longdesc = self.treestore[path][1]
        if longdesc:
            longdesc = str(longdesc)
        self.kbbrowser.explanation.set_text(longdesc)

    def _getBestObjName(self,  obj):
        '''
        @return: The best obj name possible
        '''
        if hasattr(obj, "getName"):
            name = obj.getName()
        else:
            name = repr(obj)
        return name
        
    def _filterKB(self):
        '''Filters the KB and prepares the diff to then update the GUI.
        
        @return: A dict with the diff to update the tree.
        '''
        # let's filter the real kb, to see what we should add
        filteredkb = {}

        # iterate the first layer, plugin names
#        import pdb;pdb.set_trace()
        for pluginname, plugvalues in self.fullkb.iteritems():
            holdplugin = {}
            
            # iterate the second layer, variable names
            for variabname, variabobjects in plugvalues.iteritems():
                holdvariab = {}

                # iterate the third layer, the variable objects
                if isinstance(variabobjects, list):
                    for obj in variabobjects:
                        idobject = self._getBestObjName(obj)
                        type_obj = TYPES_OBJ.get(type(obj), "misc")
                        if idobject not in holdvariab and self.filter[type_obj]:
                            if hasattr(obj, "getDesc"):
                                longdesc = obj.getDesc()
                            else:
                                longdesc = ""
                            holdvariab[idobject] = longdesc
                else:
                    # not a list, try to show it anyway (it's a misc)
                    idobject = self._getBestObjName(variabobjects)
                    if idobject not in holdvariab and self.filter["misc"]:
                        holdvariab[idobject] = ""
                
                if holdvariab:
                    holdplugin[variabname] = holdvariab
            if holdplugin:
                filteredkb[pluginname] = holdplugin
        return filteredkb

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
                treeplugin = treestore.append(None, [pluginname, ""])
                holdplugin = {}
                treeholder[pluginname] = (treeplugin, holdplugin)

            # iterate the second layer, variable names
            for variabname, variabobjects in plugvalues.iteritems():
                if variabname in holdplugin:
                    (treevariab, holdvariab) = holdplugin[variabname]
                else:
                    treevariab = treestore.append(treeplugin, [variabname, ""])
                    holdvariab = set()
                    holdplugin[variabname] = (treevariab, holdvariab)

                # iterate the third layer, the variable objects
                for (name, longdesc) in variabobjects.iteritems():
                    if name not in holdvariab:
                        holdvariab.add(name)
                        treestore.append(treevariab, [name, longdesc])
        return True
                        

class KBBrowser(gtk.HPaned):
    '''Show the Knowledge Base, with the filter and the tree.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        super(KBBrowser,self).__init__()

        # the filter to the tree
        filterbox = gtk.HBox()
        self.filters = {}
        def makeBut(label, signal, initial):
            but = gtk.CheckButton(label)
            but.set_active(initial)
            but.connect("clicked", self.typeFilter, signal)
            self.filters[signal] = initial
            but.show()
            filterbox.pack_start(but, expand=False, fill=False, padding=2)
        makeBut("Vuln", "vuln", True)
        makeBut("Info", "info", True)
        makeBut("Misc", "misc", False)
        filterbox.show()

        # the kb tree 
        self.kbtree = KBTree(self, self.filters)

        # the filter and tree box
        treebox = gtk.VBox()
        treebox.pack_start(filterbox, expand=False, fill=False)
        treebox.pack_start(self.kbtree)
        treebox.show()

        # all in the first pane
        scrollwin21 = gtk.ScrolledWindow()
        scrollwin21.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin21.add_with_viewport(treebox)
        scrollwin21.show()

        # the explanation
        explan_tv = gtk.TextView()
        explan_tv.set_editable(False)
        explan_tv.set_cursor_visible(False)
        explan_tv.set_wrap_mode(gtk.WRAP_WORD)
        self.explanation = explan_tv.get_buffer()
        explan_tv.show()
        scrollwin22 = gtk.ScrolledWindow()
        scrollwin22.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin22.add_with_viewport(explan_tv)
        scrollwin22.show()

        # pack & show
        self.pack1(scrollwin21)
        self.pack2(scrollwin22)
        self.set_position(150)
        self.show()

    def typeFilter(self, button, type):
        '''Changes the filter of the KB in the tree.'''
        self.filters[type] = button.get_active()
        self.kbtree.setFilter(self.filters)


class URLsTree(gtk.TreeView):
    '''Show the URLs that the system discovers.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        # simple empty Tree Store
        self.treestore = gtk.TreeStore(str)
        gtk.TreeView.__init__(self, self.treestore)
        #self.set_enable_tree_lines(True)

        # the TreeView column
        tvcolumn = gtk.TreeViewColumn('URLs')
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, "text", 0)
        self.append_column(tvcolumn)

        # this tree structure will keep the parents where to insert nodes
        self.treeholder = {}

        # get the queue and go live
        queue = kb.kb.getData('urls', 'urlQueue')
        self.urls = helpers.IteratedQueue(queue)
        gobject.timeout_add(500, self.addUrl().next)
        self.show()

    def addUrl(self):
        '''Adds periodically the new URLs to the tree.

        @return: True to keep being called by gobject, False when it's done.
        '''
        for url in self.urls.get():
            if url is None:
                yield True
                continue
            (scheme, netloc, path, params, query, fragment) = urllib2.urlparse.urlparse(url)
            ini = "%s://%s" % (scheme, netloc)
            end = ""
            if params:
                end += ";" + params
            if query:
                end += "?" + query
            if fragment:
                end += "#" + fragment
            nodes = path.split("/")[1:]
            nodes.insert(0, ini)
            nodes.append(end)
            parts = [x for x in nodes if x]
            self._insertNodes(None, parts, self.treeholder)
        yield False

    def _insertNodes(self, parent, parts, holder):
        '''Insert a new node in the tree.

        It's recursive: it walks the path of nodes, being each node a 
        part of the URL, checking every time if needs to create a new
        node or just enter in it.

        @param parent: the parent to insert the node
        @param parts: the rest of the parts to walk the path
        @param holder: the dict when what is already exists is stored.

        @return: The new or modified holder
        '''
        if not parts:
            return {}
        node = parts[0]
        rest = parts[1:]
        if node in holder:
            # already exists, use it if have more nodes
            (treenode, children) = holder[node]
            return self._insertNodes(treenode, rest, children)

        # does not exist, create it
        newtreenode = self.treestore.append(parent, [node])
        newholdnode = self._insertNodes(newtreenode, rest, {})
        holder[node] = (newtreenode, newholdnode)
        return holder


class ScanRunBody(gtk.VPaned):
    '''The whole body of scan run.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        super(ScanRunBody,self).__init__()

        # the paned window
        inner_hpan = gtk.HPaned()
        
        # left
        urlstree = URLsTree()
        scrollwin1 = gtk.ScrolledWindow()
        scrollwin1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin1.add_with_viewport(urlstree)
        scrollwin1.show()

        # rigth
        kbbrowser = KBBrowser()
        scrollwin2 = gtk.ScrolledWindow()
        scrollwin2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin2.add_with_viewport(kbbrowser)
        scrollwin2.show()

        # pack it all and show
        inner_hpan.pack1(scrollwin1)
        inner_hpan.pack2(scrollwin2)
        inner_hpan.set_position(250)
        inner_hpan.show()
        self.pack1(inner_hpan)

        # bottom widget
        messag = messages.Messages()
        self.pack2(messag)

        self.set_position(250)
        self.show()

