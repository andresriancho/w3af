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

# To show request and responses
from core.ui.gtkUi.reqResViewer import reqResWindow

import gobject
from . import helpers, entries


class w3afDotWindow(xdot.DotWindow):

    ui = '''
    <ui>
        <toolbar name="ToolBar">
            <toolitem action="ZoomIn"/>
            <toolitem action="ZoomOut"/>
            <toolitem action="ZoomFit"/>
            <toolitem action="Zoom100"/>
        </toolbar>
    </ui>
    '''

    def __init__(self):
        gtk.Window.__init__(self)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        
        self.graph = xdot.Graph()

        window = self

        window.set_title('HTTP Response Cluster')
        window.set_default_size(512, 512)
        vbox = gtk.VBox()
        window.add(vbox)

        self.widget = xdot.DotWidget()

        # Create a UIManager instance
        uimanager = self.uimanager = gtk.UIManager()

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        window.add_accel_group(accelgroup)

        # Create an ActionGroup
        actiongroup = gtk.ActionGroup('Actions')
        self.actiongroup = actiongroup

        # Create actions
        actiongroup.add_actions((
            ('ZoomIn', gtk.STOCK_ZOOM_IN, None, None, None, self.widget.on_zoom_in),
            ('ZoomOut', gtk.STOCK_ZOOM_OUT, None, None, None, self.widget.on_zoom_out),
            ('ZoomFit', gtk.STOCK_ZOOM_FIT, None, None, None, self.widget.on_zoom_fit),
            ('Zoom100', gtk.STOCK_ZOOM_100, None, None, None, self.widget.on_zoom_100),
        ))

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI descrption
        uimanager.add_ui_from_string(self.ui)

        # Create a Toolbar
        toolbar = uimanager.get_widget('/ToolBar')
        vbox.pack_start(toolbar, False)

        vbox.pack_start(self.widget)

        self.set_focus(self.widget)

        self.show_all()

    def set_filter(self, filter):
        self.widget.set_filter(filter)

    def set_dotcode(self, dotcode, filename='<stdin>'):
        if self.widget.set_dotcode(dotcode, filename):
            self.widget.zoom_to_fit()

class clusterGraphWidget(w3afDotWindow):
    def __init__(self, w3af, response_list):
        '''
        @parameter response_list: A list with the responses to graph.
        '''
        self.w3af = w3af
        w3afDotWindow.__init__(self)
        self.widget.connect('clicked', self.on_url_clicked)
        
        # Now I generate the dotcode based on the data
        dotcode = self._generateDotCode(response_list)
        self.set_filter('neato')
        self.set_dotcode(dotcode)

    def _xunique_combinations(self, items, n):
        if n==0: yield []
        else:
            for i in xrange(len(items)):
                for cc in self._xunique_combinations(items[i+1:],n-1):
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
        
        # Calculate the distances
        dist_dict = {}
        for r1, r2 in self._xunique_combinations(response_list, 2):
            dist_dict[(r1, r2)] = 1- relative_distance(r1.getBody(), r2.getBody() )
            
        # Normalize
        dist_dict = self._normalize_distances(dist_dict)
        
        # Write the links between them
        for r1, r2 in dist_dict:
            distance = dist_dict[(r1, r2)]
            dotcode += str(r1.getId()) + ' -- ' + str(r2.getId()) + ' [len='+str(distance)+', style=invis];\n'
        
        dotcode += '}'
        
        return dotcode

    def _normalize_distances(self, dist_dict):
        '''
        Perform some magic in order to get a nice graph
        @return: A normalized distance dict
        '''
        # Find max
        max = 0
        for d in dist_dict.values():
            if d > max:
                max = d
                
        # Find min
        min = 9999
        for d in dist_dict.values():
            if d < min:
                min = d

        # Find avg
        sum = 0
        for d in dist_dict.values():
            sum += d
        avg = sum / len(dist_dict)
        
        # Normalize
        res = {}
        for r1, r2 in dist_dict:
            actual_value = dist_dict[(r1, r2)]
            if actual_value > avg:
                new_value = avg
            else:
                new_value = actual_value
            
            if actual_value < 0.1:
                new_value = min + avg / 3
            
            res[(r1, r2)] = new_value
        
        return res
        

    def on_url_clicked(self, widget, id, event):
        '''
        When the user clicks on the node, we get here.
        @parameter id: The id of the request that the user clicked on.
        '''
        reqResWindow(self.w3af, int(id))
        return True
