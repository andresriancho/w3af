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

useMozilla = False
useGTKHtml2 = True

try:
    import gtkmozembed
    withMozillaTab = True
except Exception, e:
    withMozillaTab = False

try:
    import gtkhtml2
    withGtkHtml2 = True
except Exception, e:
    withGtkHtml2 = False
   
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
        reqResViewer = gtk.HPaned()
        resultNotebook = gtk.Notebook()
        requestNotebook = gtk.Notebook()
        
        reqLabel = gtk.Label("Request")
        self._reqPaned = requestPaned()
        resLabel = gtk.Label("Response")
        self._resPaned = responsePaned()
        
        if (withMozillaTab and useMozilla) or (withGtkHtml2 and useGTKHtml2):
            swRenderedHTML = gtk.ScrolledWindow()
            renderedLabel = gtk.Label("Rendered response")
            
            if withMozillaTab and useMozilla:
                self._renderedPaned = gtkmozembed.MozEmbed()
            if withGtkHtml2 and useGTKHtml2:
                self._renderedPaned = gtkhtml2.View()
                
            swRenderedHTML.add(self._renderedPaned)
        
        requestNotebook.append_page(self._reqPaned, reqLabel)
        reqResViewer.pack1(requestNotebook)
        resultNotebook.append_page(self._resPaned, resLabel)
        
        if (withMozillaTab and useMozilla) or (withGtkHtml2 and useGTKHtml2):
            resultNotebook.append_page(swRenderedHTML, renderedLabel)
            
        reqResViewer.pack2(resultNotebook)
        reqResViewer.set_position(400)
        reqResViewer.show_all()
        
        # Create the req/res selector (when a search with more than one result is done, this window appears)
        self._sw = gtk.ScrolledWindow()
        self._sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self._lstore = gtk.ListStore(gobject.TYPE_UINT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_UINT)
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
        self._vpan.pack2( reqResViewer )
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

        # columns for METHOD
        column = gtk.TreeViewColumn('Method', gtk.CellRendererText(),text=1)
        column.set_sort_column_id(1)
        treeview.append_column(column)

        # columns for URI
        column = gtk.TreeViewColumn('URI', gtk.CellRendererText(),text=2)
        column.set_sort_column_id(2)
        treeview.append_column(column)
        
        # columns for Code
        column = gtk.TreeViewColumn('Code', gtk.CellRendererText(),text=3)
        column.set_sort_column_id(3)
        treeview.append_column(column)
        
    def _initDB( self ):
        try:
            self._db_req_res = kb.kb.getData('gtkOutput', 'db')
        except:
            return False
        else:
            return True
    
    def _findRequestResponse( self, widget):
        if self._initDB():
            condition = self._searchText.get_text()
            if not self._searchText.validate( condition ):
                # The text that was entered by the user is not a valid search!
                pass
            else:
                    self._doSearch( condition )
        else:
            self._showDialog('No results', 'The database engine has no rows at this moment. Please start a scan.' )
    
    def _showDialog( self, title, msg, gtkLook=gtk.MESSAGE_INFO ):
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtkLook, gtk.BUTTONS_OK, msg)
        dlg.set_title( title )
        dlg.run()
        dlg.destroy()            
    
    def _doSearch( self, condition ):
        '''
        Perform a search where only one (request of response) database is involved
        '''
        toExec = 'resultList = [ r for r in self._db_req_res if %s ]' % condition
        
        try:
            exec( toExec )
        except:
            self._showDialog('Error', 'Invalid search string, please try again.', gtkLook=gtk.MESSAGE_ERROR )
        else:
            if len( resultList ) > 1:
                self._showListView( resultList )
            elif len( resultList ) == 1:
                # I got only one response to the database query!
                self.showReqResById( resultList[0].id )
            else:
                self._showDialog('No results', 'The search you performed returned no results.' )
        
    def _viewInReqResViewer( self, widget ):
        '''
        This method is called when the user clicks on one of the search results that are shown in the listview
        '''
        (path, column) = widget.get_cursor()
        itemNumber = path[0]
        
        # Now I have the item number in the lstore, the next step is to get the id of that item in the lstore
        id = self._lstore[ itemNumber ][0]
        self.showReqResById( id )
    
    def showReqResById( self, id ):
        '''
        This method should be called by other tabs when they want to show what request/response pair
        is related to the vulnerability.
        '''
        try:
            result = [ r for r in self._db_req_res if r.id == id ][0]
        except Exception, e:
            om.out.error('An exception was found while searching for the request with id: ' + str(id) + '. Exception: ' +str(e) )
        else:
            self._reqPaned.show( result.method, result.uri, result.http_version, result.request_headers, result.postdata )
            self._resPaned.show( result.http_version, result.code, result.msg, result.response_headers, result.body )
            
            if withGtkHtml2 and useGTKHtml2:
                document = gtkhtml2.Document()
                document.clear()
                document.open_stream('text/html')
                document.write_stream(result.body)
                document.close_stream()
                self._renderedPaned.set_document(document)
                
            if withMozillaTab and useMozilla:
                self._renderedPaned.render_data( res.body,long(len(res.body)), req.uri , 'text/html')
        
    def _showListView( self, results ):
        '''
        Show the results of the search in a listview
        '''
        # First I clear all old results...
        self._lstore.clear()
        
        for item in results:
            iter = self._lstore.append( [item.id, item.method, item.uri, item.code] )
        
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
        ValidatedEntry.__init__(self, value)
        self.default_value = "id == 1"
        self._match = None

    def validate(self, text):
        '''Redefinition of ValidatedEntry's method.

        @param text: the text to validate
        @return True if the text is ok.

        Validates if the text matches the regular expression
        '''
        ### WARNING !!!!
        ### Remember that this regex controls what goes into a exec() function, so, THINK about what you are doing before allowing some characters
        self._match = re.match('^(?:((?:r\\.(?:id|method|uri|http_version|request_headers|data|code|msg|response_headers|body))) (==|>|>=|<=|<|!=) ([\w\'\" /:\.]+)( (and|or) )?)*$', text )
        ### WARNING !!!!
        if self._match:
            return True
        else:
            return False

class requestResponsePaned:
    def __init__( self ):
        # The textview where a part of the req/res is showed
        self._upTv = gtk.TextView()
        self._upTv.set_border_width(5)
        
        # Scroll where the textView goes
        sw1 = gtk.ScrolledWindow()
        sw1.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        # The textview where a part of the req/res is showed
        self._downTv = gtk.TextView()
        self._downTv.set_border_width(5)
        
        # Scroll where the textView goes
        sw2 = gtk.ScrolledWindow()
        sw2.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        # Add everything to the scroll views
        sw1.add(self._upTv)
        sw2.add(self._downTv)
        
        # vertical pan (allows resize of req/res texts)
        vpan = gtk.VPaned()
        ### TODO: This should be centered
        vpan.set_position( 200 )
        vpan.pack1( sw1 )
        vpan.pack2( sw2 )
        vpan.show_all()
        
        self.add( vpan )
        
    def _clear( self, textView ):
        '''
        Clears a text view.
        '''
        buffer = textView.get_buffer()
        start, end = buffer.get_bounds()
        buffer.delete(start, end)
        
class requestPaned(gtk.HPaned, requestResponsePaned):
    def __init__(self):
        gtk.HPaned.__init__(self)
        requestResponsePaned.__init__( self )
        
    def show( self, method, uri, version, headers, postData ):
        '''
        Show the data in the corresponding order in self._upTv and self._downTv
        '''
        # Clear previous results
        self._clear( self._upTv )
        self._clear( self._downTv )
        
        buffer = self._upTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, method + ' ' + uri + ' ' + 'HTTP/' + version + '\n')
        buffer.insert( iter, headers )
        
        buffer = self._downTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, postData )
    
class responsePaned(gtk.HPaned, requestResponsePaned):
    def __init__(self):
        gtk.HPaned.__init__(self)
        requestResponsePaned.__init__( self )
        
    def show( self, version, code, msg, headers, body ):
        '''
        Show the data in the corresponding order in self._upTv and self._downTv
        '''
        # Clear previous results
        self._clear( self._upTv )
        self._clear( self._downTv )

        buffer = self._upTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, 'HTTP/' + version + ' ' + str(code) + ' ' + str(msg) + '\n')
        buffer.insert( iter, headers )
        
        buffer = self._downTv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert( iter, body )
    
