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
        self.connect("key-press-event", self._key)
        self.sclines.connect("populate-popup", self._populate_popup)
        self.textbuf = self.sclines.get_buffer()
        self.textbuf.create_tag("yellow-background", background="yellow")
        self.search_stt = "no"
        self.actualfound = 0

        self.show()

    def typeFilter(self, button, type):
        '''Applies the filter selected through the checkboxes.'''
        self.filters[type] = button.get_active()
        active_types = [k for k,v in self.filters.items() if v]
        self.sclines.filter(active_types)

    # machinery to start the search:
    #   _key: to supervise the ctrl-F and F3
    #   _populate_popup: to alter the standard popup menu
    #   _build_search: add the search widgets at the bottom
    def _key(self, widg, event):
        if event.keyval == self.key_f and event.state & gtk.gdk.CONTROL_MASK:
            self._build_search()
            return True
        # FIXME: add support for "Find Next (ctrl F)"
        # FIXME: add support for "Find Previous (ctrl G)"
        return False

    def _populate_popup(self, textview, menu):
        menu.append(gtk.SeparatorMenuItem())
        opc = gtk.MenuItem("Find...")
        menu.append(opc)
        opc.connect("activate", self._build_search)
        menu.show_all()

    def _build_search(self, widget=None):
        print "build_search"
        if self.search_stt == "builded":
            self.srchtab.show()
            return
            
        if self.search_stt != "no":
            return

        tooltips = gtk.Tooltips()
        self.srchtab = gtk.HBox()

        # label
        label = gtk.Label("Find:")
        self.srchtab.pack_start(label, expand=False, fill=False, padding=3)

        # entry
        self.search_entry = gtk.Entry()
        tooltips.set_tip(self.search_entry, "Type here the phrase you want to find")
        self.search_entry.connect("activate", self._find_next)
        self.srchtab.pack_start(self.search_entry, expand=False, fill=False, padding=3)

        # find next button
        butn = entries.SemiStockButton("Next", gtk.STOCK_GO_DOWN)
        butn.connect("clicked", self._find_next)
        tooltips.set_tip(butn, "Find the next ocurrence of the phrase")
        self.srchtab.pack_start(butn, expand=False, fill=False, padding=3)

        # find previous button
        butp = entries.SemiStockButton("Previous", gtk.STOCK_GO_UP)
        butp.connect("clicked", self._find_previous)
        tooltips.set_tip(butp, "Find the previous ocurrence of the phrase")
        self.srchtab.pack_start(butp, expand=False, fill=False, padding=3)

        # make last two buttons equally width
        wn,hn = butn.size_request()
        wp,hp = butp.size_request()
        newwidth = max(wn, wp)
        butn.set_size_request(newwidth, hn)
        butp.set_size_request(newwidth, hp)

        # close button
        close = entries.SemiStockButton("", gtk.STOCK_CLOSE)
        close.connect("clicked", self._close)
        self.srchtab.pack_end(close, expand=False, fill=False, padding=3)

        self.srchtab.show_all()
        self.pack_start(self.srchtab, expand=False, fill=False)
        self.search_stt = "builded"
        self.search_entry.grab_focus()

    # 
    # the functions that actually find the text
    #

    def _find_next(self, widg):
        self._find("next")
    def _find_previous(self, widg):
        self._find("previous")
    # FIXME: remove this two
                
    def _find(self, direction):
        print "_find", direction
        # get widgets and info
        tosearch = self.search_entry.get_text()
        textbuf = self.sclines.get_buffer()
        (ini, fin) = textbuf.get_bounds()
        alltext = textbuf.get_text(ini, fin)

        # find the positions where the phrase is found
        positions = []
        pos = 0
        while True:
            try:
                pos = alltext.index(tosearch, pos)
                fin = pos + len(tosearch)
                iterini = textbuf.get_iter_at_offset(pos)
                iterfin = textbuf.get_iter_at_offset(fin)
                positions.append((pos, fin, iterini, iterfin))
            except ValueError:
                break
            pos += 1
        if not positions:
            return

        # highlight them all
        for (ini, fin, iterini, iterfin) in positions:
            textbuf.apply_tag_by_name("yellow-background", iterini, iterfin)
        print "lenpos", len(positions)

        # find where the index in positions of actualfound
        for ind, (ini, fin, iterini, iterfin) in enumerate(positions):
            if ini > self.actualfound:
                keypos = ind
                break
        else:
            keypos = 0
        # FIXME: tratar de reemplazar actualFound por la posicion del cursor
        print "keypos", keypos
        if direction == "previous":
            keypos -= 2
            if keypos < 0:
                keypos = len(positions) + keypos
            print "newk", keypos
        
        (ini, fin, iterini, iterfin) = positions[keypos]
        textbuf.select_range(iterini, iterfin)
        self.sclines.scroll_to_iter(iterini, 0, False)
        self.actualfound = ini

        # FIXME: probar que pasa cuando lo hacemos en movimiento
        # FIXME: probar que pasa cuando no encuentra nada
        # FIXME: ver que pasa con mucho texto (prender debug)

    def _close(self, widget):
        '''Hides the search bar, and cleans the background.'''
        self.srchtab.hide()
        (ini, fin) = self.textbuf.get_bounds()
        self.textbuf.remove_tag_by_name("yellow-background", ini, fin)

