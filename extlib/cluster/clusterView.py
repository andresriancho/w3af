#!/usr/bin/env python

from cluster import *
import difflib

import os, stat, time
import pygtk
pygtk.require('2.0')
import gtk

class clusterCellData:
    
    def __init__ ( self, clusteredData ):
        '''
        @parameter clusteredData: A list of objects that are clustered.
        '''
        self._clusteredData = self._parse( clusteredData )
        self._column_names = [ 'Group %d' % i for i in xrange(len(clusteredData)) ]

        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_size_request(400, 300)
        self.window.set_title('Clustering')
        
        # Quit event.
        self.window.connect("delete_event", self.delete_event)
        
        dynamicListStoreTypes = [ str for i in xrange(len(self._column_names)) ]
        self.liststore = apply( gtk.ListStore, dynamicListStoreTypes )
        self.treeview = gtk.TreeView(self.liststore)
        
        for i, cname in enumerate( self._column_names ):
            colObject = gtk.TreeViewColumn( cname )
            self.treeview.append_column( colObject )
            textRenderer = gtk.CellRendererText()
            colObject.pack_start(textRenderer, True)
            colObject.set_attributes(textRenderer, text=i)
        
        for i in self._clusteredData:
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
                for j in xrange(largerList-len(i)):
                    i.append('')
                paddedList.append( i )
            else:
                # Its a number, create a list and pad it.
                tmp = []
                tmp.append( i )
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

def main():
    gtk.main()

def int_cmp_function( a, b):
    r = abs(a-b)
    return r
    
def str_cmp_function( a, b):
    ratio = 100 - difflib.SequenceMatcher( None, a, b ).ratio() * 100
    return ratio
    
if __name__ == "__main__":
    # First we create the cluster
    data = ['abc', 'ab','a','b','x', 'xyz', 'wju', 'ju']
    #data = [1, 100]
    cl = HierarchicalClustering(data, str_cmp_function)
    res = cl.getlevel(60)
    cl_example = clusterCellData( res )
    main()
