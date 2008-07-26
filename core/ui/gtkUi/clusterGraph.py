'''
clusterGraph.py

Copyright 2008 Andres Riancho

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

# For window creation
import gtk
import gtk.gdk

# The magic =)
from extlib.xdot import xdot as xdot
from core.controllers.misc.levenshtein import relative_distance

import gobject
from . import helpers, entries
    
class clusterGraphWidget(xdot.DotWindow):
    def __init__(self, response_list):
        '''
        @parameter response_list: A list with the responses to graph.
        '''
        xdot.DotWindow.__init__(self)
        self.widget.connect('clicked', self.on_url_clicked)
        
        # Now I generate the dotcode based on the data
        dotcode = self._generateDotCode(response_list)
        self.set_dotcode(dotcode)

    def _xcombinations(self, items, n):
        if n==0: yield []
        else:
            for i in xrange(len(items)):
                for cc in self._xcombinations(items[:i]+items[i+1:],n-1):
                    yield [items[i]]+cc

    def _generateDotCode(self, response_list):
        '''
        Generate the dotcode for the current window, based on all the responses.
        
        @parameter response_list: A list with the responses.
        '''
        dotcode = 'graph G {graph [ overlap="scale" ]\n'
        # Write the URLs
        for response in response_list:
            dotcode += str(response.getId()) + ' [URL="'+ str(response.getId()) +'"];\n'
        
        # Write the links between them
        for r1, r2 in self._xcombinations(response_list, 2):
            distance = relative_distance(r1.getBody(), r2.getBody() )
            distance = 1-distance
            distance *= 2
            if distance == 0:
                distance = 0.5
            dotcode += str(r1.getId()) + ' -- ' + str(r2.getId()) + ' [len='+str(distance)+', style=invis];\n'
        
        dotcode += '}'
        
        print dotcode
        
        return dotcode


    def on_url_clicked(self, widget, url, event):
        dialog = gtk.MessageDialog(
                parent = self, 
                buttons = gtk.BUTTONS_OK,
                message_format="%s clicked" % url)
        dialog.connect('response', lambda dialog, response: dialog.destroy())
        dialog.run()
        return True
