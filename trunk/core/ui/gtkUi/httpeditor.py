"""
httpeditor.py

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

"""
import gtk
import pango
import os
import sys

import gtksourceview2 as gtksourceview

from core.data.constants import severity
from core.ui.gtkUi.common.searchable import Searchable
from core.ui.gtkUi.encdec import EncodeDecode

SEVERITY_TO_COLOR={
    severity.INFORMATION: 'green',
    severity.LOW: 'blue',
    severity.MEDIUM: 'yellow',
    severity.HIGH: 'red'}
SEVERITY_TO_COLOR.setdefault('yellow')

class HttpEditor(gtk.VBox, Searchable):
    """Special class for editing HTTP requests/responses."""
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
        self._lm = gtksourceview.LanguageManager()
        foo = self._lm.get_search_path()
        foo.append('core' + os.path.sep+ 'ui' + os.path.sep + 'gtkUi')
        self._lm.set_search_path(foo)
        self.set_language('http')
        #b.set_highlight_syntax(True)

        self.reset_bg_color()
        for sev in SEVERITY_TO_COLOR:
            self.textView.get_buffer().create_tag(sev, background=SEVERITY_TO_COLOR[sev])
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
        lang = self._lm.get_language(name)
        b = self.textView.get_buffer()
        b.set_language(lang)

    def get_language(self, name):
        b = self.textView.get_buffer()
        l = b.get_language()
        return l.get_id()

    def get_languages(self):
        return ['http', 'html', 'xml', 'css']
        #return self._lm.get_language_ids()

    def _activate_lang(self, widg, lang):
        self.set_language(lang)

    def _populate_popup(self, textview, menu):
        menu.append(gtk.SeparatorMenuItem())
        encdec = gtk.MenuItem(_('Send selected text to Encode/Decode tool'))
        encdec.connect("activate", self._send2enc)
        menu.append(encdec)
        syntaxMenu = gtk.Menu()
        for i in self.get_languages():
            langItem = gtk.MenuItem(i)
            langItem.connect("activate", self._activate_lang, i)
            syntaxMenu.append(langItem)
        opc = gtk.MenuItem(_("Syntax highlighting"))
        opc.set_submenu(syntaxMenu)
        menu.append(opc)
        menu.show_all()
        Searchable._populate_popup(self, textview, menu)

    def _send2enc(self, w=None):
        enc = EncodeDecode(self.w3af)
        enc.paneup.setText(self.get_selected_text())
        enc.panedn.setText(self.get_selected_text())

    def clear(self):
        buf = self.textView.get_buffer()
        start, end = buf.get_bounds()
        buf.delete(start, end)

    def get_selected_text(self):
        buf = self.textView.get_buffer()
        sel = buf.get_selection_bounds()
        if sel:
            return buf.get_text(sel[0],sel[1])
        else:
            return ''

    def get_text(self, splitted=False):
        buf = self.textView.get_buffer()
        rawText = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        if not splitted:
            return rawText
        # else return turple headers+data
        headers = rawText
        data = ""
        tmp = rawText.find("\n\n")
        # It's POST!
        if tmp != -1:
            headers = rawText[0:tmp+1]
            data = rawText[tmp+2:]
            if data.strip() == "":
                data = ""
        return (headers, data)

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

        @parameter text: A text that may or may not be in UTF-8.
        @return: A text, that's in UTF-8, and can be printed in a text view
        """
        text = repr(text)
        text = text[1:-1]

        for special_char in ['\n', '\r', '\t']:
            text = text.replace( repr(special_char)[1:-1], special_char )
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
        self.textView.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("#FFFFFF"))

    def get_buffer(self):
        return self.textView.get_buffer()

