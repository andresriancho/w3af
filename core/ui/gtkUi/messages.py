'''
messages.py

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
import gtk, gobject

import core.ui.gtkUi.helpers as helpers
import core.ui.gtkUi.entries as entries
import core.data.kb.knowledgeBase as kb


def getQueueDiverter(reset=False, instance=[]):
    '''Returns only one instance of the IteratedQueue.
    
    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    if reset:
        if instance:
            del instance[:]
        return
    if not instance:
        q = kb.kb.getData("gtkOutput", "queue")
        inst = helpers.IteratedQueue(q)
        instance.append(inst)
    return instance[0]

class _LineScroller(gtk.TextView):
    '''The text view of the Messages window.

    @param active_filter: the filter active at startup.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, active_filter):
        gtk.TextView.__init__(self)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)
        self.textbuffer = self.get_buffer()
        self.show()
        self.messages = getQueueDiverter()
        self.all_messages = []
        self.active_filter = active_filter
        gobject.timeout_add(500, self.addMessage().next)

    def filter(self, filter):
        '''Applies a different filter to the textview.

        @param filter: the new filter
        '''
        self.active_filter = filter
        newtxt = "".join(x[1] for x in self.all_messages if x[0] in filter)
        self.textbuffer.set_text(newtxt)

    def addMessage(self):
        '''Adds a message to the textview.

        The message is read from the iterated queue.

        @returns: True to gobject to keep calling it, and False when all
                  it's done.
        '''
        for mess in self.messages.get():
            if mess is None:
                yield True
                continue
            # Messages are unicode, so the representation is u'abc';
            # So I have to use [2:-1]
            text = repr(mess.getMsg())[2:-1] + "\n"
            mtype = mess.getType()
            self.all_messages.append((mtype, text))
            if mtype in self.active_filter:
                iter = self.textbuffer.get_end_iter()
                self.textbuffer.insert(iter, text)
                iter = self.textbuffer.get_end_iter()
                self.scroll_to_iter(iter, False)
        yield False


class Messages(gtk.VBox):
    '''The Messages window.

    It contains the checkboxes to filter and the messages theirselves.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        super(Messages,self).__init__()

        # up row buttons
        upbox = gtk.HBox()
        self.filters = {}
        def makeBut(label, signal, initial):
            but = gtk.CheckButton(label)
            but.set_active(initial)
            but.connect("clicked", self.typeFilter, signal)
            self.filters[signal] = initial
            but.show()
            upbox.pack_start(but, expand=True, fill=False)
        makeBut("Vulnerabilities", "vulnerability", True)
        makeBut("Information", "information", True)
        makeBut("Debug", "debug", False)
        upbox.show()
        self.pack_start(upbox, expand=False, fill=False)

        # the scrolling lines
        sw_mess = gtk.ScrolledWindow()
        sw_mess.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        filter = [k for k,v in self.filters.items() if v]
        self.sclines = _LineScroller(filter)
        sw_mess.add(self.sclines)
        sw_mess.show()
        self.pack_start(sw_mess, expand=True, fill=True)

        # settings for the search machinery
        self.key_f = gtk.gdk.keyval_from_name("f")
        self.key_g = gtk.gdk.keyval_from_name("g")
        self.key_G = gtk.gdk.keyval_from_name("G")
        self.key_F3 = gtk.gdk.keyval_from_name("F3")
        self.connect("key-press-event", self._key)
        self.sclines.connect("populate-popup", self._populate_popup)
        self.textbuf = self.sclines.get_buffer()
        self.textbuf.create_tag("yellow-background", background="yellow")
        self._build_search()

        # color handling for the background of the entry
        colormap = self.get_colormap()
        self.bg_normal = colormap.alloc_color("white")
        self.bg_notfnd = colormap.alloc_color("red")

        self.show()

    def typeFilter(self, button, type):
        '''Applies the filter selected through the checkboxes.'''
        self.filters[type] = button.get_active()
        active_types = [k for k,v in self.filters.items() if v]
        self.sclines.filter(active_types)

    def _key(self, widg, event):
        '''Handles keystrokes.'''
        # ctrl-something
        if event.state & gtk.gdk.CONTROL_MASK:
            if event.keyval == self.key_f:   # -f
                self.srchtab.show_all()
                self.search_entry.grab_focus()
                self.searching = True
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
        return False

    def _populate_popup(self, textview, menu):
        '''Populates the menu with the Find item.'''
        menu.append(gtk.SeparatorMenuItem())
        opc = gtk.MenuItem("Find...")
        menu.append(opc)
        opc.connect("activate", self._build_search)
        menu.show_all()

    def _build_search(self):
        '''Builds the search bar.'''
        tooltips = gtk.Tooltips()
        self.srchtab = gtk.HBox()

        # label
        label = gtk.Label("Find:")
        self.srchtab.pack_start(label, expand=False, fill=False, padding=3)

        # entry
        self.search_entry = gtk.Entry()
        tooltips.set_tip(self.search_entry, "Type here the phrase you want to find")
        self.search_entry.connect("activate", self._find, "next")
        self.search_entry.connect("changed", self._find, "find")
        self.srchtab.pack_start(self.search_entry, expand=False, fill=False, padding=3)

        # find next button
        butn = entries.SemiStockButton("Next", gtk.STOCK_GO_DOWN)
        butn.connect("clicked", self._find, "next")
        tooltips.set_tip(butn, "Find the next ocurrence of the phrase")
        self.srchtab.pack_start(butn, expand=False, fill=False, padding=3)

        # find previous button
        butp = entries.SemiStockButton("Previous", gtk.STOCK_GO_UP)
        butp.connect("clicked", self._find, "previous")
        tooltips.set_tip(butp, "Find the previous ocurrence of the phrase")
        self.srchtab.pack_start(butp, expand=False, fill=False, padding=3)

        # make last two buttons equally width
        wn,hn = butn.size_request()
        wp,hp = butp.size_request()
        newwidth = max(wn, wp)
        butn.set_size_request(newwidth, hn)
        butp.set_size_request(newwidth, hp)

        # close button
        close = gtk.Image()
        close.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_SMALL_TOOLBAR)
        eventbox = gtk.EventBox()
        eventbox.add(close)
        eventbox.connect("button-release-event", self._close)
        self.srchtab.pack_end(eventbox, expand=False, fill=False, padding=3)

        self.pack_start(self.srchtab, expand=False, fill=False)
        self.searching = False

    def _find(self, widget, direction):
        '''Actually find the text, and handle highlight and selection.'''
        # if not searching, don't do anything
        if not self.searching:
            return

        # get widgets and info
        self._clean()
        tosearch = self.search_entry.get_text()
        if not tosearch:
            return
        (ini, fin) = self.textbuf.get_bounds()
        alltext = self.textbuf.get_text(ini, fin)

        # find the positions where the phrase is found
        positions = []
        pos = 0
        while True:
            try:
                pos = alltext.index(tosearch, pos)
            except ValueError:
                break
            fin = pos + len(tosearch)
            iterini = self.textbuf.get_iter_at_offset(pos)
            iterfin = self.textbuf.get_iter_at_offset(fin)
            positions.append((pos, fin, iterini, iterfin))
            pos += 1
        if not positions:
            self.search_entry.modify_base(gtk.STATE_NORMAL, self.bg_notfnd)
            self.textbuf.select_range(ini, ini)
            return

        # highlight them all
        for (ini, fin, iterini, iterfin) in positions:
            self.textbuf.apply_tag_by_name("yellow-background", iterini, iterfin)

        # find where's the cursor in the found items
        cursorpos = self.textbuf.get_property("cursor-position")
        for ind, (ini, fin, iterini, iterfin) in enumerate(positions):
            if ini >= cursorpos:
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
        (ini, fin, iterini, iterfin) = positions[keypos]
        self.textbuf.select_range(iterini, iterfin)
        self.sclines.scroll_to_iter(iterini, 0, False)

    def _close(self, widget, event):
        '''Hides the search bar, and cleans the background.'''
        self.srchtab.hide()
        self._clean()
        self.searching = False

    def _clean(self):
        # highlights
        (ini, fin) = self.textbuf.get_bounds()
        self.textbuf.remove_tag_by_name("yellow-background", ini, fin)

        # entry background
        self.search_entry.modify_base(gtk.STATE_NORMAL, self.bg_normal)
