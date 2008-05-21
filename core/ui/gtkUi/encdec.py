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
import urllib, base64, sha, md5


class SimpleTextView(gtk.TextView):
    def __init__(self):
        gtk.TextView.__init__(self)
        self.buffer = self.get_buffer()

    def clear(self):
        '''Clears the pane.'''
        start, end = self.buffer.get_bounds()
        self.buffer.delete(start, end)

    def setText(self, newtext):
        '''Sets a new text in the up pane.
        
        @param newtext: the new text of the pane.
        '''
        self.clear()
        iter = self.buffer.get_end_iter()
        self.buffer.insert(iter, newtext)

    def getText(self):
        '''Gets the text of the up pane.

        @returns: The text of the pane.
        '''
        start, end = self.buffer.get_bounds()
        return self.buffer.get_text(start, end)


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
        self.paneup = SimpleTextView()
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
        self.panedn = SimpleTextView()
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

    def _proc(self, inp, out, func):
        txt = inp.getText()
        try:
            new = func(txt)
        except:
            out.clear()
            self.w3af.mainwin.sb("Problem processing that string!")
        else:
            out.setText(new)
        
    def encURL(self, widg):
        '''URL Encode function.'''
        self._proc(self.paneup, self.panedn, urllib.quote)

    def encBase64(self, widg):
        '''Base64 Encode function.'''
        self._proc(self.paneup, self.panedn, base64.b64encode)

    def hashSHA1(self, widg):
        '''SHA1 Hash function.'''
        def f(t):
            s = sha.new(t)
            return s.hexdigest()
        self._proc(self.paneup, self.panedn, f)

    def hashMD5(self, widg):
        '''MD5 Hash function.'''
        def f(t):
            m = md5.new(t)
            return m.hexdigest()
        self._proc(self.paneup, self.panedn, f)

    def decURL(self, widg):
        '''URL Decode function.'''
        self._proc(self.panedn, self.paneup, urllib.unquote)

    def decBase64(self, widg):
        '''Base64 Decode function.'''
        self._proc(self.panedn, self.paneup, base64.b64decode)
