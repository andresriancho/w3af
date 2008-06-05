# -*- coding: utf8 -*-

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
import urllib, base64, sha, md5, random

class SimpleTextView(gtk.TextView):
    def __init__(self):
        gtk.TextView.__init__(self)
        self.buffer = self.get_buffer()

    def clear(self):
        '''Clears the pane.'''
        start, end = self.buffer.get_bounds()
        self.buffer.delete(start, end)

    def setText(self, newtext):
        '''Sets a new text in the pane, repr'ing it.
        
        @param newtext: the new text of the pane.
        '''
        self.clear()
        iter = self.buffer.get_end_iter()
        newtext = repr(newtext)[1:-1]
        self.buffer.insert(iter, newtext)

    def getText(self):
        '''Gets the text of the pane, un-repr'ing it.

        @returns: The text of the pane.
        '''
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end)

        parts = text.split("\\x")
        for i, part in enumerate(parts[1:]):
            try:
                carac = int(part[:2], 16)
            except ValueError:
                print "BAD String: %r" % text
                return ""
            parts[i+1] = chr(carac) + part[2:]
        return "".join(parts)


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
        tit = gtk.Label("Choose an encoding function:")
        tit.set_alignment(0.0, .5)
        tit.set_width_chars(30)
        vbox.pack_start(tit, False, False)
        cb = gtk.combo_box_new_text()
        for (lab, fnc) in _butNameFunc_enc:
            cb.append_text(lab)
            b = gtk.Button(lab)
        cb.set_active(0)
        vbox.pack_start(cb, False, False)
        b = gtk.Button("Encode")
        b.connect("clicked", self._encode, cb)
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

        # lower buttons
        vbox = gtk.VBox()
        tit = gtk.Label("Choose a decoding function:")
        tit.set_width_chars(30)
        tit.set_alignment(0.0, .5)
        vbox.pack_start(tit, False, False)
        cb = gtk.combo_box_new_text()
        for (lab, fnc) in _butNameFunc_dec:
            cb.append_text(lab)
            b = gtk.Button(lab)
        cb.set_active(0)
        vbox.pack_start(cb, False, False)
        b = gtk.Button("Decode")
        b.connect("clicked", self._decode, cb)
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
        except Exception, e:
            out.setText("ERROR: Invalid input for that operation:  "+str(e))
            self.w3af.mainwin.sb("Problem processing that string!")
        else:
            out.setText(new)
        
    def _encode(self, widg, combo):
        '''Encodes the upper text.'''
        opc = combo.get_active()
        func = _butNameFunc_enc[opc][1]
        self._proc(self.paneup, self.panedn, func)
        
    def _decode(self, widg, combo):
        '''Decodes the lower text.'''
        opc = combo.get_active()
        func = _butNameFunc_dec[opc][1]
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

def urlencode(t):
    '''Encoder doing URL Encode.

    >>> urlencode("Hola mundo")
    'Hola%20mundo'
    '''
    return urllib.quote(t)

def urldecode(t):
    '''Decoder doing URL Encode.

    >>> urldecode("Hola%20mundo")
    'Hola mundo'
    '''
    return urllib.unquote(t)

def double_urlencode(t):
    '''Encoder doing Double URL Encode.

    >>> double_urlencode("Hola mundo")
    'Hola%2520mundo'
    '''
    return urllib.quote(urllib.quote(t))

def double_urldecode(t):
    '''Decoder doing Double URL Encode.

    >>> double_urldecode("Hola%2520mundo")
    'Hola mundo'
    '''
    return urllib.unquote(urllib.unquote(t))

def hex_encoding(t):
    '''Hex encoding method.
    
    This is one of the RFC compliant ways for encoding a URL.  It is also the
    simplest method of encoding a URL. The encoding method consists of
    escaping a hexadecimal byte value for the encoded character with a '%'

    >>> hex_encoding("A")
    '%41'
    >>> hex_encoding("ABC")
    '%41%42%43'
    '''
    return "%" + "%".join(hex(ord(c))[2:] for c in t)
 
def hex_decoding(t):
    '''Hex decoding method.
    
    The reverse of Hex Encoding.

    >>> hex_decoding("%41")
    'A'
    >>> hex_decoding("%41%42%43")
    'ABC'
    '''
    nums = t[1:].split("%")
    return "".join(chr(int(n,16)) for n in nums)
 
def double_percent_hex_encoding(t):
    '''Double Percent Hex encoding method.
    
    This is based on the normal method of hex encoding.  The percent
    is encoded using hex encoding followed by the hexadecimal byte 
    value to be encoded. 

    >>> double_percent_hex_encoding("A")
    '%2541'
    >>> double_percent_hex_encoding("ABC")
    '%2541%2542%2543'
    '''
    return "%25" + "%25".join(hex(ord(c))[2:] for c in t)
 
def double_nibble_hex_encoding(t):
    '''Double Nibble Hex encoding method.
    
    This is based on the standard hex encoding method.  Each hexadecimal 
    nibble value is encoded using the standard hex encoding.

    >>> double_nibble_hex_encoding("A")
    '%%34%31'
    >>> double_nibble_hex_encoding("ABC")
    '%%34%31%%34%32%%34%33'
    '''
    parts = []
    for c in t:
        x,y = hex(ord(c))[2:]
        parts.append("%%%X%%%X" % (ord(x), ord(y)))
    return "%" + "%".join(parts) 

def first_nibble_hex_encoding(t):
    '''First Nibble Hex encoding method.
    
    This is very similar to double nibble hex encoding.  The difference is 
    that only the first nibble is encoded.

    >>> first_nibble_hex_encoding("A")
    '%%341'
    >>> first_nibble_hex_encoding("ABC")
    '%%341%%342%%343'
    '''
    parts = []
    for c in t:
        x,y = hex(ord(c))[2:]
        parts.append("%%%X%s" % (ord(x), y))
    return "%" + "%".join(parts) 

def second_nibble_hex_encoding(t):
    '''Second Nibble Hex encoding method.
    
    This is very similar to double nibble hex encoding.  The difference is 
    that only the second nibble is encoded.

    >>> second_nibble_hex_encoding("A")
    '%4%31'
    >>> second_nibble_hex_encoding("ABC")
    '%4%31%4%32%4%33'
    '''
    parts = []
    for c in t:
        x,y = hex(ord(c))[2:]
        parts.append("%s%%%X" % (x, ord(y)))
    return "%" + "%".join(parts) 

def utf8_barebyte_encoding(t):
    '''UTF-8 Barebyte Encoding, just a normal UTF-8 encoding.

    >>> utf8_barebyte_encoding("A")
    'A'
    >>> utf8_barebyte_encoding("Año")
    'A\\xc3\\xb1o'
    '''
    return t.encode("utf8")

def utf8_encoding(t):
    '''UTF-8 Encoding. Note that the exa values are shown with a '%'.

    >>> utf8_encoding("A")
    'A'
    >>> utf8_encoding("Año")
    'A%C3%B1o'
    '''
    return "".join("%%%X"%ord(x) if ord(x)>127 else x for x in t)

def msu_encoding(t):
    '''Microsoft %U Encoding.
    
    This presents a different way to encode Unicode code point values
    up to 65535 (or two bytes).  The format is simple; %U precedes 4
    hexadecimal nibble values that represent the Unicode code point value.

    >>> msu_encoding("A")
    '%U0041'
    >>> msu_encoding("Año")
    '%U0041%UC3B1%U006F'
    '''
    full = (c.encode("hex_codec").zfill(4) for c in t.decode("utf8"))
    uppr = (x.upper() for x in full)
    return "%U" + "%U".join(uppr)

def random_upper(t):
    '''Change random chars of the string to upper case.

    This function has no tests, because its random nature.
    '''
    return "".join((c.upper() if random.random()>.5 else c) for c in t)

def random_lower(t):
    '''Change random chars of the string to lower case.

    This function has no tests, because its random nature.
    '''
    return "".join((c.lower() if random.random()>.5 else c) for c in t)

def mysql_encode(t):
    '''Convert the text to a CHAR-like MySQL command.

    >>> mysql_encode("Hola mundo")
    'CHAR(72,111,108,97,32,109,117,110,100,111)'
    '''
    return "CHAR(%s)" % ",".join(str(ord(c)) for c in t)

def mssql_encode(t):
    '''Convert the text to a CHAR-like MS SQL command.

    >>> mssql_encode("Mundo")
    'CHAR(77)+CHAR(117)+CHAR(110)+CHAR(100)+CHAR(111)'
    '''
    return "CHAR(%s)" % ")+CHAR(".join(str(ord(c)) for c in t)


_butNameFunc_enc = [
    ("URL Encode",                   urlencode),
    ("Double URL Encode",            double_urlencode),
    ("Base64 Encode",                b64encode), 
    ("SHA1 Hash",                    sha_encode),
    ("MD5 Hash",                     md5_encode),
    ("Hex Encoding",                 hex_encoding),
    ("Double Percent Hex Encoding",  double_percent_hex_encoding),
    ("Double Nibble Hex Encoding",   double_nibble_hex_encoding),
    ("First Nibble Hex Encoding",    first_nibble_hex_encoding),
    ("Second Nibble Hex Encoding",   second_nibble_hex_encoding),
    ("UTF-8 Barebyte Encoding",      utf8_barebyte_encoding),
    ("UTF-8 Encoding",               utf8_encoding),
    ("Microsoft %U Encoding",        msu_encoding),
    ("Random Uppercase",             random_upper),
    ("Random Lowercase",             random_lower),
    ("MySQL Encode",                 mysql_encode),
    ("MS SQL Encode",                mssql_encode),
]

_butNameFunc_dec = [
    ("URL Decode",                   urldecode), 
    ("Double URL Decode",            double_urldecode), 
    ("Base64 Decode",                b64decode),
    ("Hex Decoding",                 hex_decoding),
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
