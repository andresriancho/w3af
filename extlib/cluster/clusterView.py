#!/usr/bin/env python

from cluster import *
import difflib

import os, stat, time
import pygtk
pygtk.require('2.0')
import gtk
import gobject

class clusterCellData:
    
    def __init__ ( self, data, clusteredData ):
        '''
        @parameter clusteredData: A list of objects that are clustered.
        '''
        self.current_path = None
        self.current_column = None
        
        self._data = data
        self._parsed_clusteredData = self._parse( clusteredData )
        self._column_names = [ 'Group %d' % i for i in xrange(len(clusteredData)) ]

        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(400, 300)
        self.window.set_title('Clustering')
        
        # Quit event.
        self.window.connect("delete_event", self.delete_event)
        
        # Start with the treeview and liststore creation
        dynamicListStoreTypes = [ str for i in xrange(len(self._column_names)) ]
        self.liststore = apply( gtk.ListStore, dynamicListStoreTypes )
        self.treeview = gtk.TreeView(self.liststore)

        # Add the "tool tips"
        popup_win = gtk.Window(gtk.WINDOW_POPUP)
        label = gtk.Label()
        popup_win.add(label)
        
        gobject.signal_new("path-cross-event", gtk.TreeView, gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (gtk.gdk.Event,))
        gobject.signal_new("column-cross-event", gtk.TreeView, gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (gtk.gdk.Event,))
        gobject.signal_new("cell-cross-event", gtk.TreeView, gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN, (gtk.gdk.Event,))
        
        self.treeview.connect("leave-notify-event", self.onTreeviewLeaveNotify, popup_win)
        self.treeview.connect("motion-notify-event", self.onTreeviewMotionNotify)
        
        self.treeview.connect("path-cross-event", self.emitCellCrossSignal)
        self.treeview.connect("column-cross-event", self.emitCellCrossSignal)
        
        self.treeview.connect("cell-cross-event", self.handlePopup, popup_win)

        self._colDict = {}
        for i, cname in enumerate( self._column_names ):
            colObject = gtk.TreeViewColumn( cname )
            self.treeview.append_column( colObject )
            textRenderer = gtk.CellRendererText()
            colObject.pack_start(textRenderer, True)
            colObject.set_attributes(textRenderer, text=i)
            # Save this for later. See FIXME below.
            self._colDict[ colObject ] = i
        
        for i in self._parsed_clusteredData:
            self.liststore.append( i )
        
        # Show it ! =)
        self.window.add(self.treeview)
        self.window.show_all()
        return
        
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
        
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False
    
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

    def _getInfoForId( self, id ):
        '''
        @return: A string with information about the request with id == id
        '''
        try:
            obj = [ i for i in self._data if i.getId() == int(id) ][0]
        except Exception, e:
            return ''
        else:
            return obj.getMethod() + ' ' + obj.getURL()
        
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
                popup_win.get_child().set_text( info )
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

def int_cmp_function( a, b):
    r = abs(a-b)
    return r
    
def str_cmp_function( a, b):
    ratio = 100 - difflib.SequenceMatcher( None, a, b ).ratio() * 100
    return ratio
    
def httpResponse_cmp_function( a, b ):
    ratio = 100 - difflib.SequenceMatcher( None, a.getData(), b.getData() ).ratio() * 100
    return ratio
    
if __name__ == "__main__":
    # First we create the cluster
    #data = ['abc', 'ab','a','b','x', 'xyz', 'wju', 'ju']
    #data = [1, 100]
    data = [ httpResponse('http://localhost/index.html', 'GET', 'my data1 looks like this and has no errors', 1),
    httpResponse('http://localhost/f00.html', 'GET', 'i love my data', 2),
    httpResponse('http://localhost/b4r.html', 'GET', 'my data likes me', 3),
    httpResponse('http://localhost/wiiii.php', 'GET', 'my data 4 is nice', 4),
    httpResponse('http://localhost/w0000.do', 'GET', 'oh! an error has ocurred!', 5)]
    
    cl = HierarchicalClustering(data, httpResponse_cmp_function)
    clusteredData = cl.getlevel(60)
    cl_example = clusterCellData( data, clusteredData )
    main()
