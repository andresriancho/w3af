'''
mozillaTab.py

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
import gtkmozembed

class mozillaTab(gtk.HPaned):
    '''
    A tab that contains a mozilla browser. In ubuntu, I must exec w3af like this:
        LD_LIBRARY_PATH=/usr/lib/firefox ./w3af -g
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, w3af):
        super(mozillaTab,self).__init__()
        
        # Create the mozilla browser object
        mozWidg = gtk.Entry(max=0)
        #mozWidg = gtkmozembed.MozEmbed()
        
        #TODO: Create a html file, and load that file, so no connections are made
        content = "<html><h1>Heading</h1>I'm some semi-random html...</html>"
        #mozWidg.render_data(content, long(len(content)), "file://.", 'text/html')
        
        # Create the URL bar
        entry = gtk.Entry(max=0)
        
        forward = gtk.Button(stock="gtk-go-forward")
        back = gtk.Button(stock="gtk-go-back")
        
        # Create the main container
        mainvbox = gtk.VBox()
        
        # Create the container that has the back and forward buttons and the URL bar
        menuHbox = gtk.HBox()
        menuHbox.pack_start( back )
        menuHbox.pack_start( forward )
        menuHbox.pack_start( entry )
        
        # Add the menuHbox and the mozilla object
        mainvbox.pack_start( menuHbox )
        mainvbox.pack_start( mozWidg )
        
        self.add( mainvbox )
        self.set_position(300)
        self.show_all()

