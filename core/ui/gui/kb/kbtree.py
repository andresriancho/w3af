'''
kbtree.py

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
'''
import gtk
import gobject
import Queue

import core.data.kb.knowledge_base as kb
from core.data.kb.vuln import Vuln
from core.data.kb.info import Info

from core.ui.gui import helpers, exploittab
from collections import namedtuple

TYPES_OBJ = {
    Vuln: "vuln",
    Info: "info",
}


class KBTree(gtk.TreeView):
    '''Show the Knowledge Base in a tree.

    :param filter: the initial filter
    :param title: the title to show
    :param strict: if the tree will show exactly what is filtered

    Regarding the strict parameter: as these structures are not as clean as
    they should in the Core, some information does not have a way to be
    determined if they fall in or out of the filter. So, with this parameter
    you control if to show them (strict=False) or not.

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, ifilter, title, strict):
        self.strict = strict
        self.w3af = w3af

        # simple empty Tree Store
        # columns: string to show; key for the plugin instance, icon,
        #          colorLevel, color, child_count
        self.treestore = gtk.TreeStore(gtk.gdk.Pixbuf, str, str,
                                       gtk.gdk.Pixbuf, int, str, str)
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

        # this structure will keep the items that were inserted into the tree
        self.treeholder = []
        self.pending_insert = Queue.Queue()
        self.need_complete_tree_update = False
        
        # here we will hold the instances, the key will be stored in the store
        self.instances = {}

        # container for exploitable vulns.
        self.exploit_vulns = {}
        
        self._exploit_instances = []
        
        # Do this only once in order to avoid a performance hit
        for exploit_name in self.w3af.plugins.get_plugin_list("attack"):
            exploit = self.w3af.plugins.get_plugin_inst("attack", exploit_name)
            self._exploit_instances.append(exploit)

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

        # make sure we update the knowledge base view
        kb.kb.add_observer(None, None, self._receive_kb_items)
        gobject.timeout_add(100, self._update_tree().next)
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

    def set_filter(self, active):
        '''Sets a new filter and update the tree.

        :param active: which types should be shown.
        '''
        self.filter = active
        self.need_complete_tree_update = True
    
    def _receive_kb_items(self, location_a, location_b, info_inst):
        '''
        Gets called by the KB when one of the plugins writes something to it.
        
        We've subscribed using kb.kb.add_observer(None, None, ...) so we'll
        get all changes.
        
        :return: None, the information we'll show to the user is stored in an
                 internal variable.
        '''
        if not isinstance(info_inst, Info):
            return
        
        obj_name = info_inst.get_name()
        obj_severity = info_inst.get_severity()
        
        obj_type = TYPES_OBJ.get(type(info_inst))
        color_tuple = (obj_type, obj_severity)
        colorlevel = helpers.KB_COLOR_LEVEL.get(color_tuple, 0)
        
        # Note that I can't use id(instance) here since the
        # instances that come here are created from the SQLite DB
        # and have different instances, even though they hold the
        # same information.
        idinstance = info_inst.get_uniq_id()
        
        vuln_id = info_inst.get_id()
        
        InfoData = namedtuple('InfoData', 'location_a location_b obj_name'\
                                          ' obj_type colorlevel idinstance'\
                                          ' severity vuln_id')
        data = InfoData(location_a, location_b, obj_name, obj_type, colorlevel,
                        idinstance, obj_severity, vuln_id)
        
        self.pending_insert.put(data)
        
    def _update_tree(self):
        '''Updates the GUI with the KB.

        :param treestore: the gui tree to updated.
        :param treeholder: a helping structure to calculate the diff.

        :return: True to keep being called by gobject.
        '''
        while True:
        
            if self.need_complete_tree_update:
                self.need_complete_tree_update = False
                self.treestore.clear()
                
                for item in self.treeholder:
                    self.pending_insert.put(item)
                
                self.treeholder = []
                yield True
        
            try:
                data = self.pending_insert.get_nowait()
            except Queue.Empty:
                pass
            else:
                # Do all the GUI stuff only if the filter is right
                if self.filter.get(data.obj_type, False):
                    self._handle_first_level(data)
                    self._handle_second_level(data)
                    self._add_info(data)
                
                # Back-end information storage for handling filters, always
                # store the information here in order to be able to process it
                # all again in case of a filter change
                self.treeholder.append(data)
                
            finally:
                yield True
    
    def _handle_first_level(self, data):
        '''
        If data.location_a is not already in the treestore, add it.
        
        If data.location_a is in the treestore, make sure we paint it the right
        color based on data.colorlevel
        
        Update the child count, keep in mind that the child count for this
        level is increased only when a new data.location_b is added.
        
        :param data: The data for the new item to add.
        '''
        contains_location_a = [d for d in self.treeholder if \
                               d.location_a == data.location_a]
        
        if not contains_location_a:
            # Add the new data to the treestore
            child_count = '( 1 )'
            color = helpers.KB_COLORS[data.colorlevel]
            store_iter = self.treestore.append(None, [None, data.location_a,
                                                      0, None, 0,
                                                      color,
                                                      child_count])
        else:
            # There's already data in location_a, need to update the
            # child count
            stored_locations_b = [d.location_b for d in self.treeholder if \
                                  d.location_a == data.location_a]
            
            store_iter = self._get_store_iter(data.location_a)
            
            if data.location_b not in stored_locations_b:
                # Update the child count 
                child_count = '( %s )' % (len(stored_locations_b) + 1)
                self.treestore[store_iter][6] = child_count
                
        # Make sure we paint it the right color, if it was originally of color
        # X and then we add a vulnerability that has a higher color level then
        # we need to "upgrade" the color
        if data.colorlevel > self.treestore[store_iter][4]:
            color = helpers.KB_COLORS[data.colorlevel] 
            self.treestore[store_iter][5] = color
    
    def _handle_second_level(self, data):
        '''
        If location_b is not already in the treestore under location_a, add it.
        
        If location_b is in the treestore, make sure we paint it the right
        color.
        
        Update the child count, keep in mind that the child count for this
        level is increased by each call to this method.
        '''
        contains_location_ab = [d for d in self.treeholder if \
                               d.location_a == data.location_a and\
                               d.location_b == data.location_b]
        
        parent = self._get_store_iter(data.location_a,
                                      new_data=data)
        
        if not contains_location_ab:
            # Add the new data to the treestore
            child_count = '( 1 )'
            color = helpers.KB_COLORS[data.colorlevel]
            store_iter = self.treestore.append(parent, [None, data.location_a,
                                                        0, None, 0,
                                                        color,
                                                        child_count])
        else:
            # There's already data in (location_a, location_b) need to update
            # the child count
            stored_locations_ab = [d.location_b for d in self.treeholder if \
                                   d.location_a == data.location_a and\
                                   d.location_b == data.location_b]
            
            store_iter = self._get_store_iter(data.location_a,
                                              data.location_b,
                                              new_data=data)
            
            # Update the child count 
            child_count = '( %s )' % (len(stored_locations_ab) + 1)
            self.treestore[store_iter][6] = child_count
                
        # Make sure we paint it the right color, if it was originally of color
        # X and then we add a vulnerability that has a higher color level then
        # we need to "upgrade" the color
        if data.colorlevel > self.treestore[store_iter][4]:
            color = helpers.KB_COLORS[data.colorlevel] 
            self.treestore[store_iter][5] = color
                
    def _add_info(self, data):
        '''
        Add the information object to the KB's third level at (location_a,
        location_b).
        
        Paint the vulnerability name using colorlevel.
        
        :return: None.
        '''
        #
        # Setup all the information to store
        #
        icon = helpers.KB_ICONS.get((data.obj_type, data.severity))
        if icon is not None:
            icon = icon.get_pixbuf()

        exploit_icon = None
        
        if data.obj_type == 'vuln':
            if self._is_exploitable(data.vuln_id):
                exploit_icon = helpers.loadIcon('STOCK_EXECUTE')
    
            self._map_exploits_to_vuln(data.vuln_id)
        
        color = helpers.KB_COLORS[data.colorlevel] 
        
        #
        # Store it!
        #
        tree_store_info = [exploit_icon, data.obj_name, data.idinstance,
                           icon, data.colorlevel, color, '']
        
        parent = self._get_store_iter(data.location_a,
                                          data.location_b,
                                          new_data=data)
        self.treestore.append(parent, tree_store_info)

    def _get_store_iter(self, location_a, location_b=None, info_name=None,
                        new_data=None):
        '''
        :return: A GtkTreeIter pointing to:
                    * location_a (mandatory)
                    * location_b (optional)
                    * info_name (optional)
        '''
        # First, and based on the data in self.treeholder generate a path
        # represented by a string
        path_lst = []
        treeholder_copy = self.treeholder[:]
        if new_data is not None: treeholder_copy.append(new_data)
        
        location_a_lst = [data.location_a for data in treeholder_copy]
        location_a_lst = list(set(location_a_lst))
        path_lst.append(location_a_lst.index(location_a))
        
        if location_b is not None:
            location_b_lst = [data.location_b for data in treeholder_copy if\
                              data.location_a == location_a]
            location_b_lst = list(set(location_b_lst))
            path_lst.append(location_b_lst.index(location_b))
            
        if info_name is not None:
            info_name_lst = [data.obj_name for data in treeholder_copy if\
                             data.location_a == location_a and\
                             data.location_b == location_b]
            path_lst.append(info_name_lst.index(info_name))
        
        # Get the iter from the treestore
        path_lst = [str(i) for i in path_lst]
        path = ':'.join(path_lst)
        try:
            return self.treestore.get_iter_from_string(path)
        except ValueError, ve:
            import pprint
            print 'Invalid path %s for %s %s %s with tree copy %s' % (path, location_a, location_b, info_name, pprint.pformat(treeholder_copy))
            raise ve
        
    def _popup(self, tv, event):
        '''Shows a menu when you right click on an object inside the kb.

        :param tv: the treeview.
        :param event: The GTK event
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
        #    vuln = self.get_instance(path)
        #    if isinstance(vuln, core.data.kb.Vuln):
        #        vulnid = vuln.get_id()
        #
        #        def go_log(w):
        #            self.w3af.mainwin.httplog.show_req_res_by_id(vulnid)
        #            self.w3af.mainwin.nb.set_current_page(4)
        #        opc.connect('activate', go_log)
        #    else:
        #        opc.set_sensitive(False)
        #    menu.show_all()
        #    ----

    def _showToolTips(self, widget, x, y, keyboard_tip, tooltip):
        '''Shows tooltip for 'exploit vulns' buttons'''
        try:
            # TODO: Why 27? Do something better here!!!
            title_height = 27
            path, tv_column, x_cell, y_cell = self.get_path_at_pos(
                x, y - title_height)
        except:
            return False
        else:
            # Make the X coord relative to the cell
            x_cell -= self.get_cell_area(path, tv_column).x
            # Get the potential vuln object
            vuln = self.get_instance(path)

            # Is the cursor over an 'exploit' icon?
            if vuln is not None and self._is_exploitable(vuln) \
            and 0 <= x_cell <= 18:
                tooltip.set_text(_("Exploit this vulnerability!"))
                self.set_tooltip_cell(tooltip, path, tv_column, None)
                return True
            return False

    def _exploitVuln(self, widg, event):
        '''Exploits row's vulnerability'''
        try:
            path, tv_column, x_cell, y_cell = self.get_path_at_pos(
                event.x, event.y)
        except:
            return False
        else:
            # Make the X coord relative to the cell
            x_cell -= self.get_cell_area(path, tv_column).x
            # Get the potential vuln object
            vuln = self.get_instance(path)

            if vuln is not None and self._is_exploitable(vuln) \
            and 0 <= x_cell <= 18:
                # Move to Exploit Tab
                self.w3af.mainwin.nb.set_current_page(3)
                # Exec the exploits for this vuln
                exploittab.effectivelyExploitAll(self.w3af,
                                                 self._get_exploits(vuln), False)
                return True
            return False

    def _changeButtonStyle(self, widget, evt):
        '''Put doctring here'''
        # TODO: Implement this.
        return False

    def get_instance(self, path):
        '''Extracts the instance from the tree.

        :param path: where the user is in the tree
        :return: The instance
        '''
        instanckey = self.treestore[path][2]
        instance = self.instances.get(instanckey)
        return instance

    def _is_exploitable(self, vuln_id):
        '''Indicantes if 'vuln' is exploitable

        :param vuln: The vuln to test.
        :return: A bool value
        '''
        vuln_id = str(vuln_id)
        if self.exploit_vulns.get(vuln_id):
            return True
        else:
            self._map_exploits_to_vuln(vuln_id)
            return vuln_id in self.exploit_vulns

    def _map_exploits_to_vuln(self, vuln_id):
        '''If 'vuln' is an exploitable vulnerability then map it to its
        exploits

        :param vuln: Potential vulnerability
        '''
        exploits = self._get_exploits(vuln_id) or []
        # Ensure the each vuln is processed only once.
        if not exploits:
            
            for exploit in self._exploit_instances:
                if exploit.can_exploit(vuln_id):
                    exploits.append(exploit.get_name())
                    
            # If found at least one exploit, add entry
            if exploits:
                self.exploit_vulns[str(vuln_id)] = exploits

    def _get_exploits(self, vuln_id):
        return self.exploit_vulns.get(str(vuln_id))
