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
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
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
        for (lab, fnc) in _butNameFunc_enc:
            b = gtk.Button(lab)
            b.connect("clicked", self._encode, fnc)
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
        for (lab, fnc) in _butNameFunc_dec:
            b = gtk.Button(lab)
            b.connect("clicked", self._decode, fnc)
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
        
    def _encode(self, widg, func):
        '''Encodes the upper text.'''
        self._proc(self.paneup, self.panedn, func)
        
    def _decode(self, widg, func):
        '''Decodes the lower text.'''
        self._proc(self.panedn, self.paneup, func)
        

# These are the encoding and decoding functions:

def sha_encode(t):
    '''Encoder using SHA1.

    >>> sha_encode("Hola mundo")
    'c083106c930790151165b95bd11860724e3836cb'
    '''
    s = sha.new(t)
    return s.hexdigest()

def md5_encode(t):
    '''Encoder using MD5.

    >>> md5_encode("Hola mundo")
    'f822102f4515609fc31927a84c6db7f8'
    '''
    m = md5.new(t)
    return m.hexdigest()

def b64encode(t):
    '''Encoder using Base64.

    >>> b64encode("Hola mundo")
    'SG9sYSBtdW5kbw=='
    '''
    return base64.b64encode(t)

def b64decode(t):
    '''Decoder using Base64.

    >>> b64decode("SG9sYSBtdW5kbw==")
    'Hola mundo'
    '''
    return base64.b64decode(t)

def urllib_quote(t):
    '''Encoder doing URL Encode.

    >>> urllib.quote("Hola mundo")
    'Hola%20mundo'
    '''
    return urllib.quote(t)

def urllib_unquote(t):
    '''Decoder doing URL Encode.

    >>> urllib.unquote("Hola%20mundo")
    'Hola mundo'
    '''
    return urllib.unquote(t)

_butNameFunc_enc = [
    ("URL Encode",    urllib_quote),
    ("Base64 Encode", b64encode), 
    ("SHA1 Hash",     sha_encode),
    ("MD5 Hash",      md5_encode),
]

_butNameFunc_dec = [
    ("URL Decode",    urllib_unquote), 
    ("Base64 Decode", b64decode),
] 


def _test_all():
    '''To use these tests, from the w3af root directory, do:

    >>> import core.ui.gtkUi.encdec
    >>> core.ui.gtkUi.encdec._test_all()
    '''
    import doctest
    glob = globals()
    for func in (x[1] for x in _butNameFunc_enc+_butNameFunc_dec):
        doctest.run_docstring_examples(func, glob)
