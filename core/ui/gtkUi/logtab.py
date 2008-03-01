'''
logtab.py

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

import pygtk
pygtk.require('2.0')
import gtk

import core.ui.gtkUi.messages as messages

class LogBody(gtk.VPaned):
    '''Body of the exploit tab.

    @param w3af: the Core instance.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(LogBody,self).__init__()
        self.w3af = w3af
        self.panels = {}

        # the paned window
        inner_hpan = gtk.HPaned()
        
        # first widget
        messag = messages.Messages()
        self.pack1(messag)

        # bottom widget
        label = gtk.Label("A graphic log in the future (we hope!)")
        self.pack2(label)

        self.set_position(300)
        self.show()
