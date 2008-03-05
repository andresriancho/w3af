'''
logVisualization.py

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

import pygtk
pygtk.require('2.0')
import gtk, gobject

import core.ui.gtkUi.helpers as helpers
import core.ui.gtkUi.entries as entries
import core.data.kb.knowledgeBase as kb

import core.data.constants.severity as severity

class logVisualization(gtk.DrawingArea):
    '''
    Defines a log visualization widget that shows an XY plot
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        super(logVisualization,self).__init__()
        #self.connect("expose_event", self.expose_cb)
        # pangolayout
        self._pangolayout = self.create_pango_layout("")
        # Style
        self._style = self.get_style()
        self._gc = self.style.fg_gc[gtk.STATE_NORMAL]
    
    def expose_cb(self, wg):
        print wg
    
    def draw_point(self, x, y, draw_severity ):
        colorMap = {severity.HIGH:'',severity.MEDIUM:'',severity.LOW:'',severity.INFORMATION:''}
        
        self.window.draw_point(self._gc, x+30, y+30)
        
        #self.draw_drawable(self._gc, pixmap, 0, 0, x+15, y+25,-1, -1)
        return
        
    def draw_title( self, x, y, text ):
        self._pangolayout.set_text(text)
        self.draw_layout(self._gc, x+5, y+50, self._pangolayout)
        return
        
