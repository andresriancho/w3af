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
import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
import re
from core.ui.gtkUi.entries import ValidatedEntry
from core.ui.gtkUi.reqResViewer import reqResViewer
from core.ui.gtkUi.reqResDBHandler import reqResDBHandler
from core.controllers.w3afException import w3afException

class httpLogTab(gtk.HPaned):
    '''
    A tab that shows all HTTP requests and responses made by the framework.    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, w3af):
        super(httpLogTab,self).__init__()
        self.w3af = w3af
        
        # Show the information message about long searchs only one time
        self._alreadyReported = True
        
        # This is a search bar for request/responses
        searchLabel = gtk.Label("Search:")
        
        # The search entry
        self._searchText = searchEntry('r.id == 1')
        self._searchText.connect("activate", self._findRequestResponse )
        
        # The button that is used to search
        searchBtn = gtk.Button(stock=gtk.STOCK_FIND)
        searchBtn.connect("clicked", self._findRequestResponse )
        
        # Create the container that has the menu
        menuHbox = gtk.HBox()
        menuHbox.set_spacing(10)
        menuHbox.pack_start( searchLabel, False )
        menuHbox.pack_start( self._searchText )
        menuHbox.pack_start( searchBtn, False )
        menuHbox.show_all()
        
        # Create the main container
        mainvbox = gtk.VBox()
        
        # Create the req/res viewer
        self._reqResViewer = reqResViewer()
        
        # Create the database handler
        self._dbHandler = reqResDBHandler()
        
        # Create the req/res selector (when a search with more than one result is done, this window appears)
        self._sw = gtk.ScrolledWindow()
        self._sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._lstore = gtk.ListStore(gobject.TYPE_UINT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_UINT, gobject.TYPE_STRING)
        # create tree view
        self._lstoreTreeview = gtk.TreeView(self._lstore)
        self._lstoreTreeview.set_rules_hint(True)
        self._lstoreTreeview.set_search_column(0)
        self.__add_columns( self._lstoreTreeview )
        self._lstoreTreeview.show()
        self._lstoreTreeview.connect('cursor-changed', self._viewInReqResViewer)
        self._sw.add(self._lstoreTreeview)
        
        # I want all sections to be resizable
        self._vpan = gtk.VPaned()
        self._vpan.pack1( self._sw )
        self._vpan.pack2( self._reqResViewer )
        self._vpan.show()
        
        # Add the menuHbox, the request/response viewer and the r/r selector on the bottom
        mainvbox.pack_start( menuHbox, False )
        mainvbox.pack_start( self._vpan )
        mainvbox.show()
        
        # Add everything
        self.add( mainvbox )
        self.set_position(300)
        self.show()
    
    def __add_columns(self, treeview):
        model = treeview.get_model()
        # column for id's
        column = gtk.TreeViewColumn('ID', gtk.CellRendererText(),text=0)
        column.set_sort_column_id(0)
        treeview.append_column(column)

        # column for METHOD
        column = gtk.TreeViewColumn('Method', gtk.CellRendererText(),text=1)
        column.set_sort_column_id(1)
        treeview.append_column(column)

        # column for URI
        column = gtk.TreeViewColumn('URI', gtk.CellRendererText(),text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)
        
        # column for Code
        column = gtk.TreeViewColumn('Code', gtk.CellRendererText(),text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)

        # column for response message
        column = gtk.TreeViewColumn('Message', gtk.CellRendererText(),text=4)
        column.set_sort_column_id(4)
        treeview.append_column(column)
    
    def _findRequestResponse( self, widget):
        try:
            searchResultObjects = self._dbHandler.searchByString( self._searchText.get_text() )
        except w3afException, w3:
            self._showDialog('No results', str(w3) )
        else:
            # Now show the results
            print searchResultObjects
            print searchResultObjects[0].id
            if len( searchResultObjects ) > 1:
                self._showListView( searchResultObjects )
            elif len( searchResultObjects ) == 1:
                # I got only one response to the database query!
                self.showReqResById( searchResultObjects[0].id )
            else:
                self._showDialog('No results', 'The search you performed returned no results.' )

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
        id = self._lstore[ itemNumber ][0]
        self.showReqResById( id )
    
    def showReqResById( self, search_id ):
        '''
        This method should be called by other tabs when they want to show what request/response pair
        is related to the vulnerability.
        '''
        result = self._dbHandler.searchById( search_id )
        if result:
            self._reqResViewer.request.show( result.method, result.uri, result.http_version, result.request_headers, result.postdata )
            self._reqResViewer.response.show( result.http_version, result.code, result.msg, result.response_headers, result.body, result.uri, 'text/html' )
        else:
            self._showDialog('Error', 'The id ' + str(id) + 'is not inside the database.')
        
    def _showListView( self, results ):
        '''
        Show the results of the search in a listview
        '''
        # First I clear all old results...
        self._lstore.clear()
        
        for item in results:
            iter = self._lstore.append( [item.id, item.method, item.uri, item.code, item.msg] )
        
        # Size search results
        if len(results) < 10:
            position = 13 + 48 * len(results)
        else:
            position = 13 + 120
            
        self._vpan.set_position(position)
        self._sw.show_all()
            
class searchEntry(ValidatedEntry):
    '''Class that inherits from validate entry in order to turn yellow if the text is not valid'''
    def __init__(self, value):
        self.default_value = "r.id == 1"
        self._match = None
        self.rrh = reqResDBHandler()
        ValidatedEntry.__init__(self, value)

    def validate(self, text):
        '''
        Validates if the text matches the regular expression
        
        @param text: the text to validate
        @return True if the text is ok.
        '''
        return self.rrh.validate( text )
