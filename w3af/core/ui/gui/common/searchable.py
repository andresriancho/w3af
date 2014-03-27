"""
searchable.py

Copyright 2010 Andres Riancho

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
import gtk
from w3af.core.ui.gui.entries import SemiStockButton


class Searchable(object):
    """Class that gives the machinery to search to a TextView.

    Just inheritate it from the box that has the textview to extend.

    :param textview: the textview to extend
    :param small: True if the buttons will only have the icons

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, textview, small=False):
        self.textview = textview
        self.small = small
        # By default, don't match case
        self._matchCaseValue = False
        # key definitions
        self.key_f = gtk.gdk.keyval_from_name("f")
        self.key_g = gtk.gdk.keyval_from_name("g")
        self.key_G = gtk.gdk.keyval_from_name("G")
        self.key_F3 = gtk.gdk.keyval_from_name("F3")
        self.key_Esc = gtk.gdk.keyval_from_name("Escape")
        # signals
        self.connect("key-press-event", self._key)
        self.textview.connect("populate-popup", self._populate_popup)
        # colors for textview and entry backgrounds
        self.textbuf = self.textview.get_buffer()
        self.textbuf.create_tag("yellow-background", background="yellow")
        colormap = self.get_colormap()
        self.bg_normal = colormap.alloc_color("white")
        self.bg_notfnd = colormap.alloc_color("red")
        # build the search tab
        self._build_search(None)

    def _key(self, widg, event):
        """Handles keystrokes."""
        # ctrl-something
        if event.state & gtk.gdk.CONTROL_MASK:
            if event.keyval == self.key_f:   # -f
                self.show_search()
            elif event.keyval == self.key_g:   # -g
                self._find(None, "next")
            elif event.keyval == self.key_G:   # -G (with shift)
                self._find(None, "previous")
            return True
        # F3
        if event.keyval == self.key_F3:
            if event.state & gtk.gdk.SHIFT_MASK:
                self._find(None, "previous")
            else:
                self._find(None, "next")
        # Esc
        if event.keyval == self.key_Esc:
            self._close(None, None)
        return False

    def _populate_popup(self, textview, menu):
        """Populates the menu with the Find item."""
        menu.append(gtk.SeparatorMenuItem())
        opc = gtk.MenuItem(_("Find..."))
        menu.append(opc)
        opc.connect("activate", self.show_search)
        menu.show_all()

    def show_search(self, widget=None):
        """Shows the search tab."""
        self.srchtab.show_all()
        self.search_entry.grab_focus()
        self.searching = True

    def _build_search(self, widget):
        """Builds the search bar."""
        self.srchtab = gtk.HBox()
        # close button
        close = gtk.Image()
        close.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        eventbox = gtk.EventBox()
        eventbox.add(close)
        eventbox.connect("button-release-event", self._close)
        self.srchtab.pack_start(eventbox, expand=False, fill=False, padding=3)
        # label
        label = gtk.Label("Find:")
        self.srchtab.pack_start(label, expand=False, fill=False, padding=3)
        # entry
        self.search_entry = gtk.Entry()
        self.search_entry.set_tooltip_text(
            _("Type here the phrase you want to find"))
        self.search_entry.connect("activate", self._find, "next")
        self.search_entry.connect("changed", self._find, "find")
        self.srchtab.pack_start(
            self.search_entry, expand=False, fill=False, padding=3)
        # find next button
        if self.small:
            but_text = ''
        else:
            but_text = 'Next'
        butn = SemiStockButton(but_text, gtk.STOCK_GO_DOWN)
        butn.connect("clicked", self._find, "next")
        butn.set_tooltip_text(_("Find the next ocurrence of the phrase"))
        self.srchtab.pack_start(butn, expand=False, fill=False, padding=3)
        # find previous button
        if self.small:
            but_text = ''
        else:
            but_text = ('Previous')
        butp = SemiStockButton(but_text, gtk.STOCK_GO_UP)
        butp.connect("clicked", self._find, "previous")
        butp.set_tooltip_text(_("Find the previous ocurrence of the phrase"))
        self.srchtab.pack_start(butp, expand=False, fill=False, padding=3)
        # make last two buttons equally width
        wn, hn = butn.size_request()
        wp, hp = butp.size_request()
        newwidth = max(wn, wp)
        butn.set_size_request(newwidth, hn)
        butp.set_size_request(newwidth, hp)
        # Match case CheckButton
        butCase = gtk.CheckButton(_('Match case'))
        butCase.set_active(self._matchCaseValue)
        butCase.connect("clicked", self._matchCase)
        # FIXME
        # current version of gtk.TextIter doesn't support SEARCH_CASE_INSENSITIVE
        #butCase.show()
        #self.srchtab.pack_start(butCase, expand=False, fill=False, padding=3)
        self.pack_start(self.srchtab, expand=False, fill=False)
        # Results
        self._resultsLabel = gtk.Label("")
        self.srchtab.pack_start(
            self._resultsLabel, expand=False, fill=False, padding=3)
        self.searching = False

    def _matchCase(self, widg):
        """
        Toggles self._matchCaseValue and searches again
        """
        self._matchCaseValue = not self._matchCaseValue
        self._find(None, 'find')

    def _find(self, widget, direction):
        """Actually find the text, and handle highlight and selection."""
        # if not searching, don't do anything
        if not self.searching:
            return
        # get widgets and info
        self._clean()
        tosearch = self.search_entry.get_text()
        if not tosearch:
            return
        positions = self.highlight(
            tosearch, "yellow-background", self._matchCaseValue)
        if not len(positions):
            return
        # find where's the cursor in the found items
        cursor = self.textbuf.get_mark("insert")
        cursorIter = self.textbuf.get_iter_at_mark(cursor)
        for ind, (iterini, iterfin) in enumerate(positions):
            if iterini.compare(cursorIter) >= 0:
                keypos = ind
                break
        else:
            keypos = 0
        # go next or previos, and adjust in the border
        if direction == "next":
            keypos += 1
            if keypos >= len(positions):
                keypos = 0
        elif direction == "previous":
            keypos -= 1
            if keypos < 0:
                keypos = len(positions) - 1
        # mark and show it
        (iterini, iterfin) = positions[keypos]
        self.textbuf.select_range(iterini, iterfin)
        self.textview.scroll_to_iter(iterini, 0, False)

    def highlight(self, text, tag='yellow-background', case_sensitive=True):
        """Find the text, and handle highlight."""

        # Before searching, I clean the text parameter, as it might contain
        # null bytes, which will trigger an error like:
        # TypeError: GtkTextIter.forward_search() argument 1 must be string without null bytes, not str
        text = str(text)
        text = text.replace('\x00', '')
        # TODO: Will the highlighting succeed? How's the text with \0's actually
        # printed in the textview?

        flags = gtk.TEXT_SEARCH_VISIBLE_ONLY
        startIter = self.textbuf.get_start_iter()
        # find the positions where the phrase is found
        positions = []
        while True:
            result = startIter.forward_search(text, flags, None)
            if result:
                positions.append((result[0], result[1]))
                startIter = result[1]
            else:
                break
        if not positions:
            self.search_entry.modify_base(gtk.STATE_NORMAL, self.bg_notfnd)
            self.textbuf.select_range(startIter, startIter)
            self._resultsLabel.set_text('')
            return positions
        self._resultsLabel.set_text(_('Total: ') + str(len(positions)))
        # highlight them all
        for (iterini, iterfin) in positions:
            self.textbuf.apply_tag_by_name(tag, iterini, iterfin)
        return positions

    def _close(self, widget, event):
        """Hides the search bar, and cleans the background."""
        self.srchtab.hide()
        self._clean()
        self.searching = False

    def _clean(self, tag='yellow-background'):
        """Cleans the entry colors."""
        # highlights
        (ini, fin) = self.textbuf.get_bounds()
        self.textbuf.remove_tag_by_name(tag, ini, fin)
        # entry background
        self.search_entry.modify_base(gtk.STATE_NORMAL, self.bg_normal)
        self._resultsLabel.set_text('')
