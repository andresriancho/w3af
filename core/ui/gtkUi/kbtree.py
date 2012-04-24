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

import gtk, gobject

import core.data.kb.knowledgeBase as kb
from . import helpers, exploittab
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
    def __init__(self, w3af, ifilter, title, strict):
        self.strict = strict
        self.w3af = w3af

        # simple empty Tree Store
        # columns: string to show; key for the plugin instance, icon, colorLevel, color, child_count
        self.treestore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, gtk.gdk.Pixbuf, int, str, str)
        gtk.TreeView.__init__(self, self.treestore)
        #self.set_enable_tree_lines(True)

        # the exploit icon (when needed), text, icon column and the child_count
        tvcol = gtk.TreeViewColumn(title)
        cell = gtk.CellRendererPixbuf()
        tvcol.pack_start(cell, expand=False)
        tvcol.add_attribute(cell, "pixbuf", 0)
        cell = gtk.CellRendererPixbuf()
        tvcol.pack_start(cell, expand=False)
        tvcol.add_attribute(cell, "pixbuf", 3)
        cell = gtk.CellRendererText()
        tvcol.pack_start(cell, expand=False)
        tvcol.add_attribute(cell, "text", 1)
        tvcol.add_attribute(cell, "foreground", 5)
        cell = gtk.CellRendererText()
        tvcol.pack_start(cell, expand=True)
        tvcol.add_attribute(cell, "text", 6)
        tvcol.add_attribute(cell, "foreground", 5)
        
        self.append_column(tvcol)

        # Sort function
        # remember that the 4 is just a number that is then used in
        # set_sort_column_id
        self.treestore.set_sort_func(4, self._treestore_sort)

        # this tree structure will keep the parents where to insert nodes
        self.treeholder = {}

        # here we will hold the instances, the key will be stored in the store
        self.instances = {}
        
        # container for exploitable vulns. 
        self.exploit_vulns = {}

        # initial filters
        self.filter = ifilter
        self.lastcheck = False

        # button events
        self.connect('button-release-event', self._popup)
        self.connect('button-press-event', self._doubleClick)
        self.connect('button-press-event', self._exploitVuln)
        
        # cursor events
        self.props.has_tooltip = True
        self.connect("query-tooltip", self._showToolTips)
##        self.connect("motion-notify-event", self._changeButtonStyle)

        # get the knowledge base and go live
        self.fullkb = kb.kb.dump()
        gobject.timeout_add(500, self._updateTree, self.treestore, self.treeholder)
        self.postcheck = False
        
        self.show()

    def _treestore_sort(self, model, iter1, iter2):
        '''
        This is a custom sort function to sort the treestore.
        
        Sort method:
            - First all red
            - Then all infos
            - Then the rest
            - Each alphabetically
        '''
        # TODO: Code this
        return 0
        
    def _doubleClick(self, widg, event):
        '''If double click, expand/collapse the row.'''
        if event.type == gtk.gdk._2BUTTON_PRESS:
            path = self.get_cursor()[0]
            # This "if path" fixed bug #2205544
            # https://sourceforge.net/tracker2/?func=detail&atid=853652&aid=2205544&group_id=170274
            if path:
                if self.row_expanded(path):
                    self.collapse_row(path)
                else:
                    self.expand_row(path, False)

    def _filterKB(self):
        '''Calculates the difference between the KB and the tree.

        This way, only is added to the tree those nodes that are new.

        @return: The filtered KB.
        '''
        # let's filter the real kb, to see what we should add
        filteredkb = {}

        # iterate the first layer, plugin names
        for pluginname, plugvalues in self.fullkb.items():
            holdplugin = {}
            maxpluginlevel = 0
            
            # iterate the second layer, variable names
            for variabname, variabobjects in plugvalues.items():
                holdvariab = []
                maxvariablevel = 0

                # iterate the third layer, the variable objects
                if isinstance(variabobjects, list):
                    for obj in variabobjects:
                        idobject = self._getBestObjName(obj)
                        type_obj = TYPES_OBJ.get(type(obj), "misc")
                        if type_obj == "vuln":
                            severity = obj.getSeverity()
                        else:
                            severity = None
                        colorlevel = helpers.KB_COLOR_LEVEL.get((type_obj, severity), 0)
                        maxvariablevel = max(maxvariablevel, colorlevel)
                        # the type must be in the filter, and be in True
                        if self.filter.get(type_obj,False): 
                            holdvariab.append((idobject, obj, type_obj, severity, helpers.KB_COLORS[colorlevel]))
                else:
                    # Not a list, try to show it anyway
                    # This is an ugly hack, because these structures in the core
                    # are not as clean as should be
                    # Use this strict parameter to decide if you will show as much
                    # as possible, or want to be strict regarding the type here
                    if not self.strict:
                        idobject = self._getBestObjName(variabobjects)
                        if self.filter["misc"]:
                            holdvariab.append((idobject, variabobjects, "misc", None, "black"))

                if holdvariab:
                    holdplugin[variabname] = (holdvariab, helpers.KB_COLORS[maxvariablevel])
                    maxpluginlevel = max(maxpluginlevel, maxvariablevel)
            if holdplugin:
                filteredkb[pluginname] = (holdplugin, helpers.KB_COLORS[maxpluginlevel])
        return filteredkb

    def setFilter(self, active):
        '''Sets a new filter and update the tree.

        @param active: which types should be shown.
        '''
        self.filter = active
        new_treestore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, gtk.gdk.Pixbuf, int, str, str)
        # Sort
        # remember that the 4 is just a number that is then used in
        # set_sort_column_id
        new_treestore.set_sort_func(4, self._treestore_sort)
        
        new_treeholder = {}
        self._updateTree(new_treestore, new_treeholder)
        self.set_model(new_treestore)
        self.treestore = new_treestore
        self.treeholder = new_treeholder
        self.exploit_vulns = {}

    def _getBestObjName(self,  obj):
        '''Gets the best possible name for the object.

        @return: The best obj name possible
        '''
        if hasattr(obj, 'getName'):
            try:
                name = obj.getName()
            except:
                name = repr(obj)
        else:
            name = repr(obj)
            
        return name
        
    def _updateTree(self, treestore, treeholder):
        '''Updates the GUI with the KB.

        @param treestore: the gui tree to updated.
        @param treeholder: a helping structure to calculate the diff.

        @return: True to keep being called by gobject.
        '''        
        # if the core is not running, don't have anything to update
        if not self.w3af.status.is_running():
            if self.lastcheck:
                return True
            else:
                self.lastcheck = True
        self.lastcheck = False


        # get the filtered knowledge base info
        filteredKB = self._filterKB()

        # Note for the following lines: we store the path in the dict, and then
        # regenerate the iter with that path, to avoid the iter to become invalid
        # when the tree changes in some way (we may use the iter later to change
        # the color)

        # iterate the first layer, plugin names
        for pluginname, (plugvalues, plugincolor) in filteredKB.items():
            if pluginname in treeholder:
                (pathplugin, holdplugin) = treeholder[pluginname]
                treeplugin = treestore.get_iter(pathplugin)
                # the color can change later!
                self.treestore[treeplugin][5] = plugincolor
                # Update the child_count
                self.treestore[treeplugin][6] = child_count = '( ' + str(len(plugvalues)) + ' )'
            else:
                child_count = '( ' + str(len(plugvalues)) + ' )'
                treeplugin = treestore.append(None, [None, pluginname, 0, None, 0, plugincolor, child_count])
                holdplugin = {}
                pathplugin = treestore.get_path(treeplugin)
                treeholder[pluginname] = (pathplugin, holdplugin)

            # iterate the second layer, variable names
            for variabname, (variabobjects, variabcolor) in plugvalues.items():
                if variabname in holdplugin:
                    (pathvariab, holdvariab) = holdplugin[variabname]
                    treevariab = treestore.get_iter(pathvariab)
                    # the color can change later!
                    self.treestore[treevariab][5] = variabcolor
                    # Update the child_count
                    self.treestore[treevariab][6] = child_count = '( ' + str(len(variabobjects)) + ' )'
                else:
                    child_count = '( ' + str(len(variabobjects)) + ' )'
                    treevariab = treestore.append(treeplugin, [None, variabname, 0, None, 0, variabcolor, child_count])
                    holdvariab = set()
                    pathvariab = treestore.get_path(treevariab)
                    holdplugin[variabname] = (pathvariab, holdvariab)

                # iterate the third layer, the variable objects
                for name,instance,obtype,severity,color in variabobjects:
                    idinstance = str(id(instance))
                    if idinstance not in holdvariab:
                        holdvariab.add(idinstance)
                        icon = helpers.KB_ICONS.get((obtype, severity))
                        if icon is not None:
                            icon = icon.get_pixbuf()
                        
                        iconExploit = helpers.loadIcon('STOCK_EXECUTE') if \
                                        self._isExploitable(instance) else None

                        treestore.append(treevariab, [iconExploit, name, idinstance,
                                                      icon, 0, color, ''])
                        self.instances[idinstance] = instance
                        self._mapExploitsToVuln(instance)
        
        # TODO: Right now I only get ValueError: invalid tree path
        # when enabling this line, and I don't know why :S
        
        # And finally sort it
        #treestore.set_sort_column_id(3, gtk.SORT_ASCENDING)
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

        # [Andres] I'm leaving this commented because I know that in the future
        # I'll want to do something similar. The code that is commented here, 
        # pop-ups a menu:
        #    ----
        #    menu = gtk.Menu()
        #    opc = gtk.MenuItem("Show HTTP request and response")
        #    menu.append(opc)
        #    menu.popup(None, None, None, event.button, event.time)
        #    # get instance
        #    vuln = self.getInstance(path)
        #    if isinstance(vuln, core.data.kb.vuln.vuln):
        #        vulnid = vuln.getId()
        #    
        #        def goLog(w):
        #            self.w3af.mainwin.httplog.showReqResById(vulnid)
        #            self.w3af.mainwin.nb.set_current_page(4)
        #        opc.connect('activate', goLog)
        #    else:
        #        opc.set_sensitive(False)
        #    menu.show_all()
        #    ----
        
    def _showToolTips(self, widget, x, y, keyboard_tip, tooltip):
        '''Shows tooltip for 'exploit vulns' buttons'''
        try:
            # TODO: Why 27? Do something better here!!!
            title_height = 27
            path, tv_column, x_cell, y_cell = self.get_path_at_pos(x, y - title_height)
        except:
            return False
        else:
            # Make the X coord relative to the cell
            x_cell -= self.get_cell_area(path, tv_column).x
            # Get the potential vuln object
            vuln = self.getInstance(path)

            # Is the cursor over an 'exploit' icon?
            if vuln is not None and self._isExploitable(vuln) \
                and 0 <= x_cell <= 18:
                tooltip.set_text(_("Exploit this vulnerability!"))
                self.set_tooltip_cell(tooltip, path, tv_column, None)
                return True
            return False
    
    def _exploitVuln(self, widg, event):
        '''Exploits row's vulnerability'''
        try:
            path, tv_column, x_cell, y_cell = self.get_path_at_pos(event.x, event.y)
        except:
            return False
        else:
            # Make the X coord relative to the cell
            x_cell -= self.get_cell_area(path, tv_column).x
            # Get the potential vuln object
            vuln = self.getInstance(path)
            
            if vuln is not None and self._isExploitable(vuln) \
                and 0 <= x_cell <= 18:
                # Move to Exploit Tab
                self.w3af.mainwin.nb.set_current_page(3)
                # Exec the exploits for this vuln
                exploittab.effectivelyExploitAll(self.w3af, \
                                                 self._getExploits(vuln), False)
                return True
            return False
    
    def _changeButtonStyle(self, widget, evt):
        '''Put doctring here'''
        # TODO: Implement this.
        return False

    def getInstance(self, path):
        '''Extracts the instance from the tree.

        @param path: where the user is in the tree
        @return: The instance
        '''
        instanckey = self.treestore[path][2]
        instance = self.instances.get(instanckey)
        return instance
    
    def _isExploitable(self, vuln):
        '''Indicantes if 'vuln' is exploitable
        
        @param vuln: The vuln to test.
        @return: A bool value
        '''
        # Ensure we're actually dealing with a vuln.
        _type = TYPES_OBJ.get(type(vuln))
        if _type != 'vuln':
            return
        
        vuln_id = str(vuln.getId())
        if self.exploit_vulns.get(vuln_id):
            return True
        else:
            self._mapExploitsToVuln(vuln)
            return self.exploit_vulns.has_key(vuln_id)
    
    def _mapExploitsToVuln(self, vuln):
        '''If 'vuln' is an exploitable vulnerability then map it to its exploits
        
        @param vuln: Potential vulnerability
        '''
        # Ensure we're actually dealing with a vuln.
        _type = TYPES_OBJ.get(type(vuln))
        if _type != 'vuln':
            return
        
        exploits = self._getExploits(vuln) or []
        # Ensure the each vuln is processed only once.
        if not exploits:
            vuln_id = vuln.getId()
            for exploit_name in self.w3af.plugins.getPluginList("attack"):
                exploit = self.w3af.plugins.getPluginInstance(exploit_name, "attack")
                if exploit.canExploit(vuln_id):
                    exploits.append(exploit_name)
            # If found at least one exploit, add entry
            if exploits:
                self.exploit_vulns[str(vuln_id)] = exploits
    
    def _getExploits(self, vuln):
        return self.exploit_vulns.get(str(vuln.getId()))
