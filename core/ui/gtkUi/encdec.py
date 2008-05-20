'''
encdec.py

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

import pygtk, gtk
import core.ui.gtkUi.helpers as helpers
import core.ui.gtkUi.entries as entries


class EncodeDecode(entries.RememberingWindow):
    '''Tool to encode and decode strings in different ways.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(EncodeDecode,self).__init__(w3af, "encodedecode", "w3af - Encode / Decode")
        self.w3af = w3af

        # splitted panes
        vpan = gtk.VPaned()

        # upper pane
        hbox = gtk.HBox()
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.paneup = gtk.TextView()
        sw.add(self.paneup)
        hbox.pack_start(sw, True, True, padding=5)

        # upper buttons
        vbox = gtk.VBox()
        buttons = [("URL Encode", "encURL"), ("Base64 Encode", "encBase64"), 
                   ("SHA1 Hash", "hashSHA1"), ("MD5 Hash", "hashMD5")]
        for (lab, fnc) in buttons:
            b = gtk.Button(lab)
            b.connect("clicked", getattr(self, fnc))
            vbox.pack_start(b, False, False)
        hbox.pack_start(vbox, False, False, padding=5)
        vpan.pack1(hbox)

        # lower pane
        hbox = gtk.HBox()
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.panedn = gtk.TextView()
        sw.add(self.panedn)
        hbox.pack_start(sw, True, True, padding=5)

        # upper buttons
        vbox = gtk.VBox()
        buttons = [("URL Decode", "decURL"), ("Base64 Decode", "decBase64")] 
        for (lab, fnc) in buttons:
            b = gtk.Button(lab)
            b.connect("clicked", getattr(self, fnc))
            vbox.pack_start(b, False, False)
        hbox.pack_start(vbox, False, False, padding=5)
        vpan.pack2(hbox)

        vpan.set_position(300)
        self.vbox.pack_start(vpan, padding=10)
        self.show_all()

    def encURL(self, widg):
        '''URL Encode function.'''
        print '''URL Encode function.'''

    def encBase64(self, widg):
        '''Base64 Encode function.'''
        print '''Base64 Encode function.'''

    def hashSHA1(self, widg):
        '''SHA1 Hash function.'''
        print '''SHA1 Hash function.'''

    def hashMD5(self, widg):
        '''MD5 Hash function.'''
        print '''MD5 Hash function.'''

    def decURL(self, widg):
        '''URL Decode function.'''
        print '''URL Decode function.'''

    def decBase64(self, widg):
        '''Base64 Decode function.'''
        print '''Base64 Decode function.'''

