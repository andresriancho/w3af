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
from core.data.db.reqResDBHandler import reqResDBHandler
from core.controllers.w3afException import w3afException

MARKUP_HELP = _('''The w3af framework saves all the requests to a database. This database can be searched using a SQL like syntax that combines the <i>id</i>, <i>url</i> and <i>code</i> columns.

Here are some <b>examples</b>:
    - <i>id = 3 or id = 4</i>
    - <i>code &lt;&gt; 404 and code &gt; 400</i>
    - <i>url like '%xc.php'</i>
    - <i>url like '%xc%' and id &lt;&gt; 3</i>
''')

class httpLogTab(entries.RememberingHPaned):
    '''
    A tab that shows all HTTP requests and responses made by the framework.    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, w3af):
        super(httpLogTab,self).__init__(w3af, "pane-httplogtab", 300)
        self.w3af = w3af
        
        # Show the information message about long searchs only one time
        self._alreadyReported = True
        
        # This is a search bar for request/responses
        searchLabel = gtk.Label(_("Search:"))
        
        # The search entry
        self._searchText = searchEntry('id = 1')
        self._searchText.connect("activate", self._findRequestResponse )
        
        # The button that is used to search
        searchBtn = gtk.Button(stock=gtk.STOCK_FIND)
        searchBtn.connect("clicked", self._findRequestResponse )
        
        # A help button
        helpBtn = gtk.Button(stock=gtk.STOCK_HELP)
        helpBtn.connect("clicked", self._showHelp )
        
        # Create the container that has the menu
        menuHbox = gtk.HBox()
        menuHbox.set_spacing(10)
        menuHbox.pack_start( searchLabel, False )
        menuHbox.pack_start( self._searchText )
        menuHbox.pack_start( searchBtn, False )
        menuHbox.pack_start( helpBtn, False )
        menuHbox.show_all()
        
        # Create the main container
        mainvbox = gtk.VBox()
        
        # Create the req/res viewer
        self._reqResViewer = reqResViewer.reqResViewer(w3af, editableRequest=False, editableResponse=False)
        self._reqResViewer.set_sensitive(False)
        
        # Create the database handler
        self._dbHandler = reqResDBHandler()
        
        # Create the req/res selector (when a search with more than one result is done, this window appears)
        self._sw = gtk.ScrolledWindow()
        self._sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._lstore = gtk.ListStore(gobject.TYPE_UINT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_UINT, gobject.TYPE_STRING, gobject.TYPE_FLOAT)
        # create tree view
        self._lstoreTreeview = gtk.TreeView(self._lstore)
        self._lstoreTreeview.set_rules_hint(True)
        self._lstoreTreeview.set_search_column(0)
        self.__add_columns( self._lstoreTreeview )
        self._lstoreTreeview.show()
        self._lstoreTreeview.connect('cursor-changed', self._viewInReqResViewer)
        self._sw.add(self._lstoreTreeview)
        self._sw.set_sensitive(False)
        self._sw.show_all()
        
        # I want all sections to be resizable
        self._vpan = entries.RememberingVPaned(w3af, "pane-swandrRV", 100)
        self._vpan.pack1( self._sw )
        self._vpan.pack2( self._reqResViewer )
        self._vpan.show()
        
        # Add the menuHbox, the request/response viewer and the r/r selector on the bottom
        mainvbox.pack_start( menuHbox, False )
        mainvbox.pack_start( self._vpan )
        mainvbox.show()
        
        # Add everything
        self.add( mainvbox )
        self.show()
    
    def __add_columns(self, treeview):
        model = treeview.get_model()
        
        # column for id's
        column = gtk.TreeViewColumn(_('ID'), gtk.CellRendererText(),text=0)
        column.set_sort_column_id(0)
        treeview.append_column(column)

        # column for METHOD
        column = gtk.TreeViewColumn(_('Method'), gtk.CellRendererText(),text=1)
        column.set_sort_column_id(1)
        treeview.append_column(column)

        # column for URI
        renderer = gtk.CellRendererText()
        renderer.set_property( 'ellipsize', pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn('URI' + ' ' * 155, renderer,text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        treeview.append_column(column)
        
        # column for Code
        column = gtk.TreeViewColumn(_('Code'), gtk.CellRendererText(),text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)

        # column for response message
        column = gtk.TreeViewColumn(_('Message'), gtk.CellRendererText(),text=4)
        column.set_sort_column_id(4)
        column.set_resizable(True)
        treeview.append_column(column)
        
        # column for response time
        column = gtk.TreeViewColumn(_('Time (ms)'), gtk.CellRendererText(),text=5)
        column.set_sort_column_id(5)
        treeview.append_column(column)
    
    def _showHelp(self,  widget):
        '''
        Show a little help for the window.
        '''
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK)
        dlg.set_markup(MARKUP_HELP)
        dlg.set_title( 'Search help' )
        dlg.run()
        dlg.destroy()
    
    def _findRequestResponse( self, widget):
        try:
            searchResultObjects = self._dbHandler.searchByString( self._searchText.get_text() )
        except w3afException, w3:
            self._reqResViewer.request.clearPanes()
            self._reqResViewer.response.clearPanes()
            self._reqResViewer.set_sensitive(False)
            self._sw.set_sensitive(False)
            self._lstore.clear()
            self._showDialog(_('No results'), str(w3) )
        else:
            # no results ?
            if len( searchResultObjects ) == 0:
                self._reqResViewer.request.clearPanes()
                self._reqResViewer.response.clearPanes()
                self._reqResViewer.set_sensitive(False)
                self._sw.set_sensitive(False)
                self._lstore.clear()
                self._showDialog(_('No results'), _('The search you performed returned no results.') )
                return
            elif len( searchResultObjects ) > 10000:
                self._reqResViewer.request.clearPanes()
                self._reqResViewer.response.clearPanes()
                self._reqResViewer.set_sensitive(False)
                self._sw.set_sensitive(False)
                self._lstore.clear()
                msg = _('The search you performed returned too many results (') + str(len(searchResultObjects)) + ').\n'
                msg += _('Please refine your search and try again.')
                self._showDialog('Too many results', msg )
                return
            else:
                # show the results in the list view (when first row is selected that just triggers
                # the req/resp filling.
                self._sw.set_sensitive(True)
                self._reqResViewer.set_sensitive(True)
                self._showListView( searchResultObjects )
                self._lstoreTreeview.set_cursor((0,))
                return

    def _showDialog( self, title, msg, gtkLook=gtk.MESSAGE_INFO ):
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtkLook, gtk.BUTTONS_OK, msg)
        dlg.set_title( title )
        dlg.run()
        dlg.destroy()            
        
    def _viewInReqResViewer( self, widget ):
        '''
        This method is called when the user clicks on one of the search results that are shown in the listview
        '''
        (path, column) = widget.get_cursor()
        itemNumber = path[0]
        
        # Now I have the item number in the lstore, the next step is to get the id of that item in the lstore
        iid = self._lstore[ itemNumber ][0]
        self.showReqResById( iid )
    
    def showReqResById( self, search_id ):
        '''
        This method should be called by other tabs when they want to show what request/response pair
        is related to the vulnerability.
        '''
        search_result = self._dbHandler.searchById( search_id )
        if len(search_result) == 1:
            request, response = search_result[0]
            self._reqResViewer.request.showObject( request )
            self._reqResViewer.response.showObject( response )
        else:
            self._showDialog(_('Error'), _('The id ') + str(search_id) + _('is not inside the database.'))
        
    def _showListView( self, results ):
        '''
        Show the results of the search in a listview
        '''
        # First I clear all old results...
        self._lstore.clear()
        
        for item in results:
            request, response = item
            self._lstore.append( [response.getId(), request.getMethod(), request.getURI(), \
                                                    response.getCode(), response.getMsg(), response.getWaitTime()] )
        
        # Size search results
        if len(results) < 10:
            position = 13 + 48 * len(results)
        else:
            position = 13 + 120
            
        self._vpan.set_position(position)
        self._sw.show_all()
            
class searchEntry(entries.ValidatedEntry):
    '''Class that inherits from validate entry in order to turn yellow if the text is not valid'''
    def __init__(self, value):
        self.default_value = "id = 1"
        self._match = None
        self.rrh = reqResDBHandler()
        entries.ValidatedEntry.__init__(self, value)
        self.set_tooltip_markup(MARKUP_HELP)        

    def validate(self, text):
        '''
        Validates if the text matches the regular expression
        
        @param text: the text to validate
        @return True if the text is ok.
        '''
        return self.rrh.validate( text )
