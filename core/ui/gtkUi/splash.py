'''
splash.py

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

try:
    import pygtk
    pygtk.require('2.0')
    import gtk, gobject
except:
    print 'You have to install pygtk version >=2 to be able to run the GTK user interface. On Debian based distributions: apt-get install python-gtk2'
    sys.exit( 1 )

class Splash(gtk.Window):
    '''Builds the Splash window.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        super(Splash,self).__init__()
        vbox = gtk.VBox()
        self.add(vbox)

        # content
        img = gtk.image_new_from_file('core/ui/gtkUi/data/splash.png')
        vbox.pack_start(img)
        self.label = gtk.Label()
        vbox.pack_start(self.label)

        # color and position
        self.set_decorated(False)
        color = gtk.gdk.color_parse('#f2f2ff')
        self.modify_bg(gtk.STATE_NORMAL, color)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_size_request(505,260)

        # ensure it is rendered immediately
        self.show_all()
        while gtk.events_pending():
            gtk.main_iteration()

    def push(self, text):
        '''New text to be shown in the Splash.'''
        self.label.set_text(text)
        while gtk.events_pending():
            gtk.main_iteration()
