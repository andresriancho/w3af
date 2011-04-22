'''
httpLogTab.py

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
import gobject
import pango

# The elements to create the req/res viewer
from . import reqResViewer, entries
from core.ui.gtkUi.entries import EasyTable
from core.ui.gtkUi.entries import wrapperWidgets
from core.data.db.history import HistoryItem
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.data.options.preferences import Preferences
from core.data.options.option import option as Option
from core.data.options.comboOption import comboOption
from core.data.options.optionList import optionList

class httpLogTab(entries.RememberingHPaned):
    '''A tab that shows all HTTP requests and responses made by the framework.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, w3af, padding=10, time_refresh=False):
        """Init object."""
        super(httpLogTab,self).__init__(w3af, "pane-httplogtab", 300)
        self.w3af = w3af
        self._padding = padding
        self._lastId = 0
        self._historyItem = HistoryItem()
        if time_refresh:
            gobject.timeout_add(1000, self.refreshResults)
        # Create the main container
        mainvbox = gtk.VBox()
        mainvbox.set_spacing(self._padding)
        # Add the menuHbox, Req/Res viewer and the R/R selector on the bottom
        self._initSearchBox(mainvbox)
        self._initFilterBox(mainvbox)
        self._initReqResViewer(mainvbox)
        mainvbox.show()
        # Add everything
        self.add(mainvbox)
        self.show()

    def _initReqResViewer(self, mainvbox):
        """Create the req/res viewer."""
        self._reqResViewer = reqResViewer.reqResViewer(self.w3af,
                editableRequest=False, editableResponse=False)
        self._reqResViewer.set_sensitive(False)
        # Create the req/res selector (when a search with more 
        # than one result is done, this window appears)
        self._sw = gtk.ScrolledWindow()
        self._sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._lstore = gtk.ListStore(gobject.TYPE_UINT,gobject.TYPE_BOOLEAN,
                gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING,
                gobject.TYPE_UINT, gobject.TYPE_STRING,
                gobject.TYPE_UINT, gobject.TYPE_STRING,gobject.TYPE_FLOAT)
        # Create tree view
        self._lstoreTreeview = gtk.TreeView(self._lstore)
        self._lstoreTreeview.set_rules_hint(True)
        self._lstoreTreeview.set_search_column(0)
        self.__add_columns( self._lstoreTreeview )
        self._lstoreTreeview.show()
        self._lstoreTreeview.connect('cursor-changed', self._viewInReqResViewer)
        # Popup menu
        self._rightButtonMenu = None
        self._lstoreTreeview.connect('button-press-event', self._popupMenu)
        #
        # 
        # Selection
        #
        treeselection = self._lstoreTreeview.get_selection()
        treeselection.set_mode(gtk.SELECTION_MULTIPLE)

        self._sw.add(self._lstoreTreeview)
        #self._sw.set_sensitive(False)
        self._sw.show_all()
        # I want all sections to be resizable
        self._vpan = entries.RememberingVPaned(self.w3af, "pane-swandrRV", 100)
        self._vpan.pack1(self._sw)
        self._vpan.pack2(self._reqResViewer)
        self._vpan.show()
        mainvbox.pack_start(self._vpan)

    def _popupMenu( self, tv, event ):
        '''Generate and show popup menu.'''
        if event.button != 3:
            return
        # creates the whole menu only once
        if self._rightButtonMenu is None:
            gm = gtk.Menu()
            self._rightButtonMenu = gm
            # the items
            e = gtk.MenuItem(_("Delete selected items"))
            e.connect('activate', self._deleteSelected)
            gm.append(e)
            gm.show_all()
        else:
            gm = self._rightButtonMenu
        gm.popup( None, None, None, event.button, event.time)
        return True

    def _deleteSelected(self, widg=None):
        '''Delete selected transactions.'''
        ids = []
        iters = []
        sel = self._lstoreTreeview.get_selection()
        (model, pathlist) = sel.get_selected_rows()
        for path in pathlist:
            iters.append(self._lstore.get_iter(path))
            itemNumber = path[0]
            iid = self._lstore[itemNumber][0]
            ids.append(iid)
        for i in iters:
            self._lstore.remove(i)
        #  TODO Move this action to separate thread
        for iid in ids:
            self._historyItem.delete(iid)

    def _initSearchBox(self, mainvbox):
        """Init Search box."""
        # The search entry
        self._searchText = gtk.Entry()
        self._searchText.connect("activate", self.findRequestResponse)
        # The button that is used to advanced search
        filterBtn = gtk.ToggleButton(label=_("_Filter Options"))
        filterBtn.connect("toggled", self._showHideFilterBox)
        filterImg = gtk.Image()
        filterImg.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_MENU)
        filterBtn.set_image(filterImg)
        # Clear button
        close = gtk.Image()
        close.set_from_stock(gtk.STOCK_CLEAR , gtk.ICON_SIZE_MENU)
        clearBox = gtk.EventBox()
        clearBox.add(close)
        clearBox.connect("button-release-event", self._showAllRequestResponses)
        # Create the container that has the menu
        menuHbox = gtk.HBox()
        menuHbox.set_spacing(self._padding)
        menuHbox.pack_start(gtk.Label(_("Search:")), False)
        menuHbox.pack_start(self._searchText)
        menuHbox.pack_start(clearBox, False)
        menuHbox.pack_start(filterBtn, False)
        menuHbox.show_all()
        mainvbox.pack_start(menuHbox, False, True)

    def _initFilterBox(self, mainvbox):
        """Init advanced search options."""
        self._advSearchBox = gtk.HBox()
        self._advSearchBox.set_spacing(self._padding)
        self.pref = FilterOptions(self)
        # Filter options
        self._filterMethods = [
                ('GET', 'GET', False),
                ('POST', 'POST', False),
                ]
        filterMethods = optionList()
        for method in self._filterMethods:
            filterMethods.add(Option(method[0], method[2], method[1], "boolean"))
        self.pref.addSection('methods', _('Request Method'), filterMethods)
        filterId = optionList()
        filterId.add(Option("min", "0", "Min ID", "string"))
        filterId.add(Option("max", "0", "Max ID", "string"))
        self.pref.addSection('trans_id', _('Transaction ID'), filterId)
        filterCodes = optionList()
        codes = [
                ("1xx", "1xx", False),
                ("2xx", "2xx", False),
                ("3xx", "3xx", False),
                ("4xx", "4xx", False),
                ("5xx", "5xx", False),
                ]
        for code in codes:
            filterCodes.add(Option(code[0], code[2], code[1], "boolean"))
        self.pref.addSection('codes', _('Response Code'), filterCodes)
        filterTags = optionList()
        filterTags.add(Option("tag", False, "Tag", "boolean"))
        self.pref.addSection('commented', _('Commented'), filterTags)
        filterTypes = optionList()
        self._filterTypes = [
                ('html', 'HTML', False),
                ('javascript', 'JavaScript', False),
                ('image', 'Images', False),
                ('flash', 'Flash', False),
                ('css', 'CSS', False),
                ('text', 'Text', False),
                ]
        for filterType in self._filterTypes:
            filterTypes.add(Option(filterType[0], filterType[2], filterType[1], "boolean"))
        self.pref.addSection('types', _('Response Content Type'), filterTypes)
        filterSize = optionList()
        filterSize.add(Option("resp_size", False, "Not Null", "boolean"))
        self.pref.addSection('sizes', _('Response Size'), filterSize)
        self.pref.show()
        self._advSearchBox.pack_start(self.pref, False, False)
        self._advSearchBox.hide_all()
        mainvbox.pack_start(self._advSearchBox, False, False)

    def __add_columns(self, treeview):
        """Add columns to main log table."""
        model = treeview.get_model()
        # Column for id's
        column = gtk.TreeViewColumn(_('ID'), gtk.CellRendererText(),text=0)
        column.set_sort_column_id(0)
        treeview.append_column(column)
        
        # Column for bookmark
        #TODO: Find a better way to do this. The "B" and the checkbox aren't nice
        #what we aim for is something like the stars in gmail.
        '''
        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self.toggleBookmark, model)
        column = gtk.TreeViewColumn(_('B'), renderer)
        column.add_attribute(renderer, "active", 1)
        column.set_sort_column_id(1)
        treeview.append_column(column)
        '''
        
        # Column for METHOD
        column = gtk.TreeViewColumn(_('Method'), gtk.CellRendererText(),text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)
        # Column for URI
        renderer = gtk.CellRendererText()
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn('URI', renderer, text=3)
        column.set_sort_column_id(3)
        column.set_expand(True)
        column.set_resizable(True)
        treeview.append_column(column)
        # Column for Tag
        renderer = gtk.CellRendererText()
        #renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        renderer.set_property('editable', True)
        renderer.connect('edited', self.editTag, model)
        column = gtk.TreeViewColumn(_('Tag'), renderer, text=4)
        column.set_sort_column_id(4)
        column.set_resizable(True)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        treeview.append_column(column)
        extColumns = [
                (5, _('Code')),
                (6, _('Message')),
                (7, _('Content-Length')),
                (8, _('Content-Type')),
                (9, _('Time (ms)')),
                ]
        for n, title in extColumns:
            column = gtk.TreeViewColumn(title, gtk.CellRendererText(),text=n)
            column.set_sort_column_id(n)
            treeview.append_column(column)

    def toggleBookmark(self, cell, path, model):
        """Toggle bookmark."""
        model[path][1] = not model[path][1]
        historyItem = HistoryItem()
        historyItem.load(model[path][0])
        historyItem.toggleMark(True)
        return

    def editTag(self, cell, path, new_text, model):
        """Edit tag."""
        model[path][4] = new_text
        historyItem = HistoryItem()
        historyItem.load(model[path][0])
        historyItem.updateTag(new_text, True)
        return

    def _showHideFilterBox(self, widget):
        """Show/hide advanced options."""
        if not widget.get_active():
            self._advSearchBox.hide_all()
        else:
            self._advSearchBox.show_all()

    def _showAllRequestResponses(self, widget=None, event=None):
        """Show all results."""
        self._searchText.set_text("")
        try:
            self.findRequestResponse()
        except w3afException, w3:
            self._emptyResults()
        return

    def refreshResults(self):
        self.findRequestResponse(refresh=True)
        return True

    def findRequestResponse(self, widget=None, refresh=False):
        """Find entries (req/res)."""
        searchText = self._searchText.get_text()
        searchText = searchText.strip()
        searchData = []
        #  
        #  Search part
        #
        if searchText:
            likePieces = []
            likePieces.append(('url', "%"+searchText+"%", 'like'))
            likePieces.append(('tag', "%"+searchText+"%", 'like'))
            searchData.append((likePieces, 'OR'))
        # 
        # Filter part
        #
        # Codes
        codes = self.pref.getOptions('codes')
        filterCodes = []
        for opt in codes:
            if opt.getValue():
                codef = opt.getName()
                filterCodes.append(('codef', int(codef[0]), '='))
        searchData.append((filterCodes, 'OR'))
        # IDs
        try:
            minId = int(self.pref.getValue('trans_id', 'min'))
        except:
            minId = 0
        try:
            maxId = int(self.pref.getValue('trans_id', 'max'))
        except:
            maxId = 0
        if maxId > 0:
            searchData.append(('id', maxId, "<"))
        if minId > 0:
            searchData.append(('id', minId, ">"))
        if refresh:
            searchData.append(('id', self._lastId, ">"))
        # Sizes
        if self.pref.getValue('sizes', 'resp_size'):
            searchData.append(('response_size', 0, ">"))
        # Tags
        if self.pref.getValue('commented', 'tag'):
            searchData.append(('tag', '', "!="))
        # Content type
        filterTypes = []
        for filterType in self._filterTypes:
            if self.pref.getValue('types', filterType[0]):
                filterTypes.append(('content_type', "%"+filterType[0]+"%", 'like'))
        searchData.append((filterTypes, 'OR'))
        # Method
        filterMethods = []
        for method in self._filterMethods:
            if self.pref.getValue('methods', method[0]):
                filterTypes.append(('method', method[0], '='))
        searchData.append((filterMethods, 'OR'))

        try:
            # Please see the 5000 below
            searchResultObjects = self._historyItem.find(searchData,
                    resultLimit=5001, orderData=[("id","")])
        except w3afException, w3:
            self._emptyResults()
            return
        if len(searchResultObjects) == 0:
            if not refresh:
                self._emptyResults()
            return
        # Please see the 5001 above
        elif len(searchResultObjects) > 5000:
            self._emptyResults()
            msg = _('The search you performed returned too many results (') +\
                    str(len(searchResultObjects)) + ').\n'
            msg += _('Please refine your search and try again.')
            self._showMessage('Too many results', msg)
            return
        else:
            # show the results in the list view (when first row is selected 
            # that just triggers the req/resp filling.
            lastItem = searchResultObjects[-1]
            self._lastId = int(lastItem.id)
            self._showListView(searchResultObjects, appendMode=refresh)
            if not refresh:
                self._sw.set_sensitive(True)
                self._reqResViewer.set_sensitive(True)
                self._lstoreTreeview.set_cursor((0,))
            return

    def _emptyResults(self):
        """Empty all panes."""
        self._reqResViewer.request.clearPanes()
        self._reqResViewer.response.clearPanes()
        self._reqResViewer.set_sensitive(False)
        self._sw.set_sensitive(False)
        self._lstore.clear()

    def _showListView(self, results, appendMode=False):
        """Show the results of the search in a listview."""
        # First I clear all old results...
        if not appendMode:
            self._lstore.clear()
        for item in results:
            self._lstore.append([item.id, item.mark, item.method, item.url,
                item.tag, item.code, item.msg, item.responseSize,item.contentType,
                item.time])
        # Size search results
        if len(results) < 10:
            position = 13 + 48 * len(results)
        else:
            position = 13 + 120
        #self._vpan.set_position(position)
        if not appendMode:
            self._sw.show_all()

    def _showMessage(self, title, msg, gtkLook=gtk.MESSAGE_INFO):
        """Show message to user as GTK dialog."""
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtkLook, gtk.BUTTONS_OK, msg)
        dlg.set_title(title)
        dlg.run()
        dlg.destroy()

    def _viewInReqResViewer(self, widget):
        """Action for "onselect" event of the main listview."""
        (path, column) = widget.get_cursor()
        itemNumber = path[0]
        # Now I have the item number in the lstore, 
        # the next step is to get the id of that item in the lstore
        iid = self._lstore[itemNumber][0]
        self.showReqResById(iid)

    def showReqResById(self, search_id):
        """This method should be called by other tabs when
        they want to show what request/response pair
        is related to the vulnerability.
        """
        historyItem = self._historyItem.read(search_id)
        if historyItem:
            self._reqResViewer.request.showObject(historyItem.request)
            self._reqResViewer.response.showObject(historyItem.response)
            if historyItem.info:
                buff = self._reqResViewer.info.get_buffer()
                buff.set_text(historyItem.info)
                self._reqResViewer.info.show()
            else:
                self._reqResViewer.info.hide()
            self._reqResViewer.set_sensitive(True)
        else:
            self._showMessage(_('Error'), _('The id ') + str(search_id) +\
                    _('is not inside the database.'))

class FilterOptions(gtk.HBox, Preferences):
    def __init__(self, parentWidg):
        gtk.HBox.__init__(self)
        Preferences.__init__(self)
        self.set_spacing(10)
        self.parentWidg = parentWidg

    def show(self):
        # Init options
        self._initOptionsView()
        super(FilterOptions,self).show()

    def _initOptionsView(self):
        tooltips = gtk.Tooltips()
        for section, optList in self.options.items():
            frame = gtk.Frame()
            label = gtk.Label('<b>%s</b>' % self.sections[section])
            label.set_use_markup(True)
            label.show()
            frame.set_label_widget(label)
            frame.set_shadow_type(gtk.SHADOW_OUT)
            frame.show()
            table = EasyTable(len(optList), 2)
            for i, opt in enumerate(optList):
                titl = gtk.Label(opt.getDesc())
                titl.set_alignment(xalign=0.0, yalign=0.5)
                widg = wrapperWidgets[opt.getType()](self._changedWidget, opt)
                titl.set_mnemonic_widget(widg)
                opt.widg = widg
                tooltips.set_tip(widg, opt.getHelp())
                table.autoAddRow(titl, widg)
                table.show()
            frame.add(table)
            self.pack_start(frame, False, False)

    def _changedWidget(self, widg, like_initial):
        # check if all widgets are valid
        invalid = []
        for section, optList in self.options.items():
            for opt in optList:
                if hasattr(opt.widg, "isValid"):
                    if not opt.widg.isValid():
                        invalid.append(opt.getName())
        if invalid:
            msg = _("The configuration can't be saved, there is a problem in the following parameter(s):\n\n")
            msg += "\n-".join(invalid)
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            dlg.set_title(_('Configuration error'))
            dlg.run()
            dlg.destroy()
            return

        # Get the value from the GTK widget and set it to the option object
        for section, optList in self.options.items():
            for opt in optList:
                opt.setValue(opt.widg.getValue())
        self.parentWidg.findRequestResponse()
