"""
httpeditor.py

Copyright 2008 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import os
import re

import gtk
import pango
import gtksourceview2 as gtksourceview
from w3af import ROOT_PATH
from w3af.core.data.constants import severity
from w3af.core.ui.gui.common.searchable import Searchable
from w3af.core.ui.gui.tools.encdec import EncodeDecode


SEVERITY_TO_COLOR = {
    severity.INFORMATION: 'green',
    severity.LOW: 'blue',
    severity.MEDIUM: 'yellow',
    severity.HIGH: 'red'}
SEVERITY_TO_COLOR.setdefault('yellow')


class HttpEditor(gtk.VBox, Searchable):
    """
    Special class for editing HTTP requests/responses.
    """

    HTTP_HEAD_BODY_SPLIT_RE = re.compile('(\r\n\r\n|\n\n)')

    def __init__(self, w3af):
        gtk.VBox.__init__(self)
        self.is_request = True
        self.w3af = w3af
        # Create the textview where the text is going to be shown
        self.textView = gtksourceview.View(gtksourceview.Buffer())
        # User controlled options
        self.textView.set_highlight_current_line(False)
        self.textView.set_show_line_numbers(False)
        # Other options
        # Font
        self.set_wrap(True)
        self.textView.set_border_width(5)
        fontDesc = pango.FontDescription('monospace')
        if fontDesc:
            self.textView.modify_font(fontDesc)
        
        # Syntax highlight
        self._lang_man = gtksourceview.LanguageManager()
        spath = self._lang_man.get_search_path()
        spath.append(os.path.join(ROOT_PATH, 'core', 'ui', 'gui'))
        self._lang_man.set_search_path(spath)
        self.set_language('http')
        #b.set_highlight_syntax(True)

        self.reset_bg_color()
        for sev in SEVERITY_TO_COLOR:
            self.textView.get_buffer(
            ).create_tag(sev, background=SEVERITY_TO_COLOR[sev])
        self.textView.show()
        # Scroll where the textView goes
        sw1 = gtk.ScrolledWindow()
        sw1.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw1.add(self.textView)
        sw1.show()
        self.pack_start(sw1, expand=True, fill=True)
        # Create the search widget
        Searchable.__init__(self, self.textView, small=True)
    
    #
    # Interface
    #
    def set_language(self, name):
        lang = self._lang_man.get_language(name)
        b = self.textView.get_buffer()
        b.set_language(lang)

    def get_language(self, name):
        b = self.textView.get_buffer()
        l = b.get_language()
        return l.get_id()

    def get_string_payloads(self):
        """Give the list of payloads.
        Taken from: http://ha.ckers.org/xss.html
        """
        return [
            '";!--\'<XSS>=&{()}\\xss<script>alert(document.cookie)</script>',
            """';alert(String.fromCharCode(88,83,83))//\\\';alert(String.fromCharCode(88,83,83))//";alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//--></SCRIPT>">'><SCRIPT>alert(String.fromCharCode(88,83,83))</SCRIPT>""",
            '<SCRIPT SRC=http://ha.ckers.org/xss.js></SCRIPT>',
            '<IMG """><SCRIPT>alert("XSS")</SCRIPT>">',
            '<SCRIPT/SRC="http://ha.ckers.org/xss.js"></SCRIPT>',
            '<<SCRIPT>alert("XSS");//<</SCRIPT>',
            """<SCRIPT>a=/XSS/alert(a.source)</SCRIPT>""",
            '\\";alert(\'XSS\');//'
        ]

    def _insert_payload(self, widg, payload):
        b = self.get_buffer()
        b.insert_at_cursor(payload)

    def get_languages(self):
        return ['http', 'html', 'xml', 'css', 'js']

    def _activate_lang(self, widg, lang):
        self.set_language(lang)

    def _populate_popup(self, textview, menu):
        menu.append(gtk.SeparatorMenuItem())
        # Enc/Dec
        encdec = gtk.MenuItem(_('Send selected text to Encode/Decode tool'))
        encdec.connect("activate", self._send2enc)
        menu.append(encdec)
        # Syntax menu
        syntaxMenu = gtk.Menu()
        for i in self.get_languages():
            langItem = gtk.MenuItem(i)
            langItem.connect("activate", self._activate_lang, i)
            syntaxMenu.append(langItem)
        opc = gtk.MenuItem(_("Syntax highlighting"))
        opc.set_submenu(syntaxMenu)
        menu.append(opc)
        # Strings payloads
        payloadMenu = gtk.Menu()
        for i in self.get_string_payloads():
            payloadItem = gtk.MenuItem(i[:50] + ' ...')
            payloadItem.connect("activate", self._insert_payload, i)
            payloadMenu.append(payloadItem)
        opc = gtk.MenuItem(_("String payloads"))
        opc.set_submenu(payloadMenu)
        menu.append(opc)
        menu.show_all()
        Searchable._populate_popup(self, textview, menu)

    def _send2enc(self, w=None):
        enc = EncodeDecode(self.w3af)
        enc.paneup.set_text(self.get_selected_text())
        enc.panedn.set_text(self.get_selected_text())

    def clear(self):
        buf = self.textView.get_buffer()
        start, end = buf.get_bounds()
        buf.delete(start, end)

    def get_selected_text(self):
        buf = self.textView.get_buffer()
        sel = buf.get_selection_bounds()
        if sel:
            return buf.get_text(sel[0], sel[1])
        else:
            return ''

    def get_text(self):
        buf = self.textView.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter())

    def get_split_text(self):
        raw_text = self.get_text()
        
        # else return tuple: (headers, data)
        split_raw_text = self.HTTP_HEAD_BODY_SPLIT_RE.split(raw_text, 1)
        split_raw_text = [r.strip() for r in split_raw_text]

        if len(split_raw_text) == 1:
            # no postdata
            headers = split_raw_text[0]
            data = ''
        else:
            # We'll always have 2 here, since we passed 1 as a second
            # parameter to split
            headers = split_raw_text[0]
            data = split_raw_text[2]
                
        return headers, data
    
    def set_text(self, text, fixUtf8=False):
        buf = self.textView.get_buffer()
        if fixUtf8:
            #buf.set_text(self._to_utf8(text))
            buf.set_text(text)
        else:
            buf.set_text(text)

    def set_editable(self, e):
        return self.textView.set_editable(e)
    
    #
    # Inherit SourceView methods
    #

    def set_highlight_syntax(self, val):
        b = self.textView.get_buffer()
        b.set_highlight_syntax(val)

    def set_highlight_current_line(self, val):
        self.textView.set_highlight_current_line(val)

    def set_show_line_numbers(self, val):
        self.textView.set_show_line_numbers(val)

    def set_wrap(self, val):
        if val:
            self.textView.set_wrap_mode(gtk.WRAP_WORD)
        else:
            self.textView.set_wrap_mode(gtk.WRAP_NONE)
            
    #
    # Private methods
    #
    def _to_utf8(self, text):
        """
        This method was added to fix:

        GtkWarning: gtk_text_buffer_emit_insert: assertion `g_utf8_validate (text, len, NULL)'

        :param text: A text that may or may not be in UTF-8.
        :return: A text, that's in UTF-8, and can be printed in a text view
        """
        text = repr(text)
        text = text[1:-1]

        for special_char in ['\n', '\r', '\t']:
            text = text.replace(repr(special_char)[1:-1], special_char)
        text = text.replace("\\'", "'")
        text = text.replace('\\\\"', '\\"')
        return text

    def get_iter_at_offset(self, position):
        return self.textView.get_buffer().get_iter_at_offset(position)

    def apply_tag_by_name(self, tag, start, end):
        return self.textView.get_buffer().apply_tag_by_name(tag, start, end)

    def set_border_width(self, b):
        return self.textView.set_border_width(b)

    def set_bg_color(self, color):
        self.textView.modify_base(gtk.STATE_NORMAL, color)

    def reset_bg_color(self):
        self.textView.modify_base(
            gtk.STATE_NORMAL, gtk.gdk.color_parse("#FFFFFF"))

    def get_buffer(self):
        return self.textView.get_buffer()
