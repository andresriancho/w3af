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


# Constants that define the distance available distance functions
LEVENSHTEIN = 0
CONTENT_LENGTH = 1
HTTP_RESPONSE = 2

SELECT_HELP = """\
<b>Clustering method selection</b>

The framework provides different clustering methods. Each method defines a way in which 
the distance between two different HTTP responses is going to be calculated. The distance 
between the HTTP responses is then used to group the responses and create the clusters.

Please select the clustering method:
"""

class distance_function_selector(entries.RememberingWindow):
    '''A small window to select which distance_function the w3afDotWindow
    will use to generate the graph.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, w3af, response_list):
        super(distance_function_selector,self).__init__(
            w3af, "distance_function_selector", "w3af - Select distance function",
            "select_distance_function")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
        self.resize( 300, 200 )
        
        # Save for later usage
        self.w3af = w3af
        self.data = response_list

        # Create a label that explains what this window is all about
        helplabel = gtk.Label()
        helplabel.set_selectable(False)
        helplabel.set_markup(SELECT_HELP)
        helplabel.show()
        self.vbox.pack_start(helplabel, True, True, 0)

        # The vbox where everything is stored
        box2 = gtk.VBox(False, 10)
        box2.set_border_width(10)
        self.vbox.pack_start(box2, True, True, 0)
        box2.show()

        # Adding the radio buttons
        self._levenshtein_button = gtk.RadioButton(None, "Levenshtein distance of the HTTP bodies")
        self._levenshtein_button.set_active(True) # This one is the default
        box2.pack_start(self._levenshtein_button, True, True, 0)
        self._levenshtein_button.show()

        self._cl_button = gtk.RadioButton(self._levenshtein_button, "Content Lengths")
        box2.pack_start(self._cl_button, True, True, 0)
        self._cl_button.show()

        self._http_res_button = gtk.RadioButton(self._cl_button, "HTTP response codes")
        box2.pack_start(self._http_res_button, True, True, 0)
        self._http_res_button.show()

        separator = gtk.HSeparator()
        self.vbox.pack_start(separator, False, True, 0)
        separator.show()

        box2 = gtk.VBox(False, 10)
        box2.set_border_width(10)
        self.vbox.pack_start(box2, False, True, 0)
        box2.show()

        # And the select button at the end
        button = gtk.Button("Select")
        button.connect_object("clicked", self._launch_graph_generator, None)
        box2.pack_start(button, True, True, 0)
        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()
        
        # Show!
        button.show()
        
        # Show the window
        self.show()
        
    def _launch_graph_generator(self, widget):
        '''
        The button action.
        Launch the graph window!
        
        @return: None
        '''
        selected_function = None
        if self._cl_button.get_active():
            selected_function = CONTENT_LENGTH
        elif self._levenshtein_button.get_active():
            selected_function = LEVENSHTEIN
        elif self._http_res_button.get_active():
            selected_function = HTTP_RESPONSE
        
        # Don't show the window anymore
        self.hide()
        
        # Create the new window, with the graph
        window = clusterGraphWidget(self.w3af, self.data, distance_function=selected_function)
        window.connect('destroy', gtk.main_quit)
        gtk.main()
        
        # Quit myself, my job is done.
        self.quit(None, None)
        
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

        # Add a UI description
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
    def __init__(self, w3af, response_list, distance_function=LEVENSHTEIN):
        '''
        @parameter response_list: A list with the responses to graph.
        '''
        self.w3af = w3af
        w3afDotWindow.__init__(self)
        self.widget.connect('clicked', self.on_url_clicked)
        
        # Now I generate the dotcode based on the data
        if distance_function == LEVENSHTEIN:
            dotcode = self._generateDotCode(response_list, distance_function=self._relative_distance)
        elif distance_function == HTTP_RESPONSE:
            dotcode = self._generateDotCode(response_list, distance_function=self._http_code_distance)
        elif distance_function == CONTENT_LENGTH:
            dotcode = self._generateDotCode(response_list, distance_function=self._response_length_distance)
        else:
            raise Exception('Please review your buggy code ;)')
        
        self.set_filter('neato')
        
        # The problem with the delay is HERE ! The self._generateDotCode method is FAST.
        # The real problem is inside "tokens = graphparser.parseString(data)" (dot_parser.py)
        # which is called inside set_dotcode
        self.set_dotcode(dotcode)

    def _relative_distance(self, a, b):
        '''
        Calculates the distance between two responses based on the levenshtein distance
        
        @return: The distance
        '''
        return 1 - relative_distance(a.getBody(), b.getBody())
        
    def _http_code_distance(self, a, b):
        '''
        Calculates the distance between two responses based on the HTTP response code
        
        @return: The distance
        '''
        distance = 0.1
        for i in [100, 200, 300, 400, 500]:
            if a.getCode() in xrange(i, i+100) and not b.getCode() in xrange(i, i+100):
                distance = 1
                return distance
        return distance

    def _response_length_distance(self, a, b):
        '''
        Calculates the distance between two responses based on the length of the response body
        
        @return: The distance
        '''
        distance = abs(len(b.getBody()) - len(a.getBody()))
        distance = distance % 100
        distance = distance / 100.0
        
        return distance

    def _xunique_combinations(self, items, n):
        if n==0: yield []
        else:
            for i in xrange(len(items)):
                for cc in self._xunique_combinations(items[i+1:],n-1):
                    yield [items[i]]+cc

    def _generateDotCode(self, response_list, distance_function=relative_distance):
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
            dist_dict[(r1, r2)] = distance_function(r1, r2)
            
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
        min = dist_dict.values()[0]
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
