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

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, active_filter):
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

        entries.Searchable.__init__(self)
        self.show()

    def typeFilter(self, button, type):
        '''Applies the filter selected through the checkboxes.'''
        self.filters[type] = button.get_active()
        active_types = [k for k,v in self.filters.items() if v]
        self.sclines.filter(active_types)
