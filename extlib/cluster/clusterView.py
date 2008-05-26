#!/usr/bin/env python

from cluster import HierarchicalClustering
import difflib

import os, stat, time
import pygtk
pygtk.require('2.0')
import gtk
import gobject

    
class clusterCellWindow:
    def __init__ ( self ):
        '''
        A window that stores the clusterCellData and the level changer.
        '''
        # First we create the data
        data = [ httpResponse('http://localhost/index.html', 'GET', 'my data1 looks like this and has no errors', 1),
        httpResponse('http://localhost/f00.html', 'GET', 'i love my data', 2),
        httpResponse('http://localhost/b4r.html', 'GET', 'my data likes me', 3),
        httpResponse('http://localhost/wiiii.php', 'GET', 'my data 4 is nice', 4),
        httpResponse('http://localhost/w0000.do', 'GET', 'oh! an error has ocurred!', 5)]
        
        # The level used in the process of clustering
        self._level = 50
        
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(400, 400)
        self.window.set_title('HTTP Response object clustering')

        # Quit event.
        self.window.connect("delete_event", self.delete_event)
        
        # Create the main vbox
        main_vbox = gtk.VBox()
        
        # Create the distance pager
        dist_hbox = gtk.HBox()
        
        distanceLabel = gtk.Label()
        distanceLabel.set_text('Distance between clusters: ')
        
        distanceBackButton = gtk.Button(stock=gtk.STOCK_GO_BACK)
        distanceBackButton.connect("clicked", self._go_back)

        self._distanceLabelNumber = gtk.Label()
        self._distanceLabelNumber.set_text( str(self._level) )
        
        distanceNextButton = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        distanceNextButton.connect("clicked", self._go_forward)
        
        dist_hbox.pack_start( distanceLabel )
        dist_hbox.pack_start( distanceBackButton )
        dist_hbox.pack_start( self._distanceLabelNumber )
        dist_hbox.pack_start( distanceNextButton )
        main_vbox.pack_start(dist_hbox, False, False)
        
        # Create the widget that shows the data
        cl_data_widget = clusterCellData( data, level=self._level )
        
        # I'm going to store the cl_data_widget inside this scroll window
        _sw = gtk.ScrolledWindow()
        _sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        _sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        _sw.add( cl_data_widget )
        main_vbox.pack_start( _sw )
        
        self.window.add( main_vbox )
        self.window.show_all()
        return

    def _go_back( self, i ):
        if self._level != 10:
            self._level -= 10
        self._distanceLabelNumber.set_text( str(self._level) )        

    def _go_forward( self, i ):
        if self._level != 100:
            self._level += 10
        self._distanceLabelNumber.set_text( str(self._level) ) 
        
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

class clusterCellData(gtk.TreeView):
    def _httpResponse_cmp_function( self, a, b ):
        ratio = 100 - difflib.SequenceMatcher( None, a.getData(), b.getData() ).ratio() * 100
        return ratio
    
    def __init__ ( self, data, level=50 ):
        '''
        @parameter clusteredData: A list of objects that are clustered.
        '''
        # Save the data
        self._data = data
        
        # Create the clusters
        cl = HierarchicalClustering(data, self._httpResponse_cmp_function)
        clusteredData = cl.getlevel( level )
        
        self._parsed_clusteredData = self._parse( clusteredData )
        self._column_names = [ 'Group %d' % i for i in xrange(len(clusteredData)) ]

        # Start with the treeview and liststore creation
        dynamicListStoreTypes = [ str for i in xrange(len(self._column_names)) ]
        self.liststore = apply( gtk.ListStore, dynamicListStoreTypes )
        
        gtk.TreeView.__init__( self, self.liststore )
        
        # Internal variables
        self.current_path = None
        self.current_column = None

        self._colDict = {}
        for i, cname in enumerate( self._column_names ):
            colObject = gtk.TreeViewColumn( cname )
            self.append_column( colObject )
            textRenderer = gtk.CellRendererText()
            colObject.pack_start(textRenderer, True)
            colObject.set_attributes(textRenderer, text=i)
            # Save this for later. See FIXME below.
            self._colDict[ colObject ] = i
        
        for i in self._parsed_clusteredData:
            self.liststore.append( i )
        
        self._add_tooltip_support()
        
        # Show it ! =)
        self.show_all()
        
    def _add_tooltip_support( self ):
        # Add the "tool tips"
        popup_win = gtk.Window(gtk.WINDOW_POPUP)
        label = gtk.Label()
        popup_win.add(label)
        
        gobject.signal_new("path-cross-event", gtk.TreeView, gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (gtk.gdk.Event,))
        gobject.signal_new("column-cross-event", gtk.TreeView, gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (gtk.gdk.Event,))
        gobject.signal_new("cell-cross-event", gtk.TreeView, gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (gtk.gdk.Event,))
        
        self.connect("leave-notify-event", self.onTreeviewLeaveNotify, popup_win)
        self.connect("motion-notify-event", self.onTreeviewMotionNotify)
        
        self.connect("path-cross-event", self.emitCellCrossSignal)
        self.connect("column-cross-event", self.emitCellCrossSignal)
        
        self.connect("cell-cross-event", self.handlePopup, popup_win)
        
        # Handle double click on a row
        self.connect("row-activated", self.handleDoubleClick )    
        
    def _parse( self, clusteredData ):
        '''
        Takes a list like this one:
            [1 , 3, [4,5], [4, 5, 5], 9 ]
        
        It first creates a list like this one:
            [ [1, '', ''] ,
              [3, '', ''],
              [4, 5, ''],
              [4, 5, 5],
              [9, '', '']
            ]
        
        And finally it transposes it in order to return it.
            [ [1, 3, 4, 4, 9], 
              ['', '', 5, 5, ''],
              ['', '', '', 5, '']
            ]
        '''
        # First we find the largest list inside the original list
        largerList = [ len(i) for i in clusteredData if isinstance( i, type([]) ) ]
        largerList.sort()
        largerList.reverse()
        
        if len(largerList) == 0:
            # We don't have lists inside this list!
            largerList = 0
        else:
            largerList = largerList[0]
            
        paddedList = []
        for i in clusteredData:
            if isinstance( i, type([]) ):
                # We have a list to pad
                i = [ w.getId() for w in i]
                for j in xrange(largerList-len(i)):
                    i.append('')
                paddedList.append( i )
            else:
                # Its an object, create a list and pad it.
                tmp = []
                tmp.append( i.getId() )
                for j in xrange(largerList-len(tmp)):
                    tmp.append('')
                paddedList.append( tmp )
        
        # transpose
        resList = [ [ '' for w in range(len( paddedList ) ) ] for i in range(len( paddedList [0] ) ) ]
        
        for x, paddedList in enumerate(paddedList):
            for y, paddedItem in enumerate( paddedList ):
                resList[y][x] = str(paddedItem)
        return resList
            
    def onTreeviewLeaveNotify(self, treeview, event, popup_win):
        self.current_column = None
        self.current_path = None
        popup_win.hide()
    
    def onTreeviewMotionNotify(self, treeview, event):
    
        current_path, current_column = self.getCurrentCellData(treeview, event)[:2]
        
        if self.current_path != current_path:
            self.current_path = current_path
            treeview.emit("path-cross-event", event)
        
        if self.current_column != current_column:
            self.current_column = current_column
            treeview.emit("column-cross-event", event)
    
    def getCurrentCellData(self, treeview, event):
    
        try:
            current_path, current_column = treeview.get_path_at_pos(int(event.x), int(event.y))[:2]
        except:
            return (None, None, None, None, None, None)
            
        current_cell_area = treeview.get_cell_area(current_path, current_column)
        treeview_root_coords = treeview.get_bin_window().get_origin()
        
        cell_x = treeview_root_coords[0] + current_cell_area.x
        cell_y = treeview_root_coords[1] + current_cell_area.y
        
        cell_x_ = cell_x + current_cell_area.width
        cell_y_ = cell_y + current_cell_area.height
        
        return (current_path, current_column, cell_x, cell_y, cell_x_, cell_y_)

    def handleDoubleClick(self, treeview, path, view_column):
        # FIXME: I'm sure there is another way to do this... but... what a hell... nobody reads the code ;)
        # I'm talking about the self._colDict[ current_column ]!
        currentId = self.liststore[ path[0] ][ self._colDict[ view_column ] ]
        # Search the Id and show the data
        print 'I should show the data for',currentId, 'in a different window.'
    
    def _getInfoForId( self, id ):
        '''
        @return: A string with information about the request with id == id
        '''
        try:
            obj = [ i for i in self._data if i.getId() == int(id) ][0]
        except Exception, e:
            return ''
        else:
            return '<b><i>Method:</i></b>' + obj.getMethod() + '\n<b><i>URI:</i></b>' + obj.getURL()
        
    def handlePopup(self, treeview, event, popup_win):
        current_path, current_column, cell_x, cell_y, cell_x_, cell_y_ = self.getCurrentCellData(treeview, event)
        if cell_x != None:
            # Search the Id and show the data
            # FIXME: I'm sure there is another way to do this... but... what a hell... nobody reads the code ;)
            # I'm talking about the self._colDict[ current_column ]!
            currentId = self.liststore[ current_path[0] ][ self._colDict[ current_column ] ]
            info = self._getInfoForId( currentId )
            if not info:
                # hide!
                popup_win.hide()
            else:
                # Use the info and display the window
                popup_win.get_child().set_markup( info )
                popup_width, popup_height = popup_win.get_size()
                pos_x, pos_y = self.computeTooltipPosition(treeview, cell_x, cell_y, cell_x_, cell_y_, popup_width, popup_height, event)
                popup_win.move(int(pos_x) , int(pos_y))
                popup_win.show_all()
        else:
            popup_win.hide()
    
    def emitCellCrossSignal(self, treeview, event):
        treeview.emit("cell-cross-event", event)
    
    def computeTooltipPosition(self, treeview, cell_x, cell_y, cell_x_, cell_y_, popup_width, popup_height, event):
        screen_width = gtk.gdk.screen_width()
        screeen_height = gtk.gdk.screen_height()
    
        pos_x = treeview.get_bin_window().get_origin()[0] + event.x - popup_width/2
        if pos_x < 0:
            pos_x = 0
        elif pos_x + popup_width > screen_width:
            pos_x = screen_width - popup_width
            
        pos_y = cell_y_ + 3
        if pos_y + popup_height > screeen_height:
            pos_y = cell_y - 3 - popup_height
        
        return (pos_x , pos_y)

class httpResponse:
    def __init__( self, url, method, data, id ):
        self._url = url
        self._method = method
        self._id = id
        self._data = data
    
    def getId( self ): return self._id
    def getMethod( self ): return self._method
    def getURL( self ): return self._url
    def getData( self ): return self._data
        
def main():
    gtk.main()

if __name__ == "__main__":
    cl_win = clusterCellWindow()
    main()
