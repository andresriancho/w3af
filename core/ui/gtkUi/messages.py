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

import gtk, gobject
from . import helpers, entries
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

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, active_filter, possible):
        '''
        @param active_filter: the filter active at startup.
        '''
        gtk.TextView.__init__(self)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)
        self.textbuffer = self.get_buffer()
        self.show()
        self.messages = getQueueDiverter()
        self.all_messages = []
        self.possible = set(possible)
        self.active_filter = active_filter
        self.text_position = 0

        # colors
        self.textbuffer.create_tag("red-fg",  foreground="red")
        self.textbuffer.create_tag("blue-fg", foreground="blue")
        self.textbuffer.create_tag("brown-fg", foreground="brown")
        self.bg_colors = {
            "vulnerability": "red-fg",
            "information": "blue-fg",
            "error": "brown-fg",
        }

        gobject.timeout_add(500, self.addMessage().next)

    def filter(self, filtinfo):
        '''Applies a different filter to the textview.

        @param filtinfo: the new filter
        '''
        self.active_filter = filtinfo
        self.textbuffer.set_text("")
        for (mtype, text) in self.all_messages:
            if mtype in filtinfo:
                colortag = self.bg_colors[mtype]
                iterl = self.textbuffer.get_end_iter()
                self.textbuffer.insert_with_tags_by_name(iterl, text, colortag)
        self.scroll_to_mark(self.textbuffer.get_insert(), 0)

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
            text = "[%s] %s\n" % (mess.getTime(), mess.getMsg())
            mtype = mess.getType()

            # only store it if it's of one of the possible filtered
            if mtype not in self.possible:
                continue

            # store it
            self.all_messages.append((mtype, text))
            antpos = self.text_position
            self.text_position += len(text)

            if mtype in self.active_filter:
                iterl = self.textbuffer.get_end_iter()
                colortag = self.bg_colors[mtype]
                self.textbuffer.insert_with_tags_by_name(iterl, text, colortag)
                self.scroll_to_mark(self.textbuffer.get_insert(), 0)

        yield False


class Messages(gtk.VBox, entries.Searchable):
    '''The Messages window.

    It contains the checkboxes to filter and the messages theirselves.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self):
        gtk.VBox.__init__(self)

        # up row buttons
        upbox = gtk.HBox()
        self.filters = {}
        def makeBut(label, signal, initial):
            but = gtk.CheckButton(label)
            but.set_active(initial)
            but.connect("clicked", self.typeFilter, signal)
            self.filters[signal] = initial
            but.show()
            upbox.pack_start(but, False, False)
        makeBut("Vulnerabilities", "vulnerability", True)
        makeBut("Information", "information", True)
        makeBut("Error", "error", True)
        upbox.show()
        self.pack_start(upbox, expand=False, fill=False)

        # the scrolling lines
        sw_mess = gtk.ScrolledWindow()
        sw_mess.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        newfilter = [k for k,v in self.filters.items() if v]
        possible = self.filters.keys()
        self.sclines = _LineScroller(newfilter, possible)
        sw_mess.add(self.sclines)
        sw_mess.show()
        self.pack_start(sw_mess, expand=True, fill=True)
        
        entries.Searchable.__init__(self, self.sclines)
        self.show()

    def typeFilter(self, button, ptype):
        '''Applies the filter selected through the checkboxes.'''
        self.filters[ptype] = button.get_active()
        active_types = [k for k,v in self.filters.items() if v]
        self.sclines.filter(active_types)
