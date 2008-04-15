'''
logtab.py

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

import pygtk, gtk, gobject
import core.ui.gtkUi.messages as messages
import time


class LogGraph(gtk.DrawingArea):
    '''Defines a log visualization widget that shows an XY plot

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        self.w3af = w3af
        super(LogGraph,self).__init__()
#        self.area.set_size_request(400, 300)
        self.pangolayout = self.create_pango_layout("")

        # get the messages
        self.messages = messages.getQueueDiverter()
        self.all_messages = []

        # control variables
        self.countingPixel = 0
        self.alreadyStopped = False
        self.pixelQuant = 0
        self.timeGrouping = 1000

        # schedule the message adding, and go live!
        gobject.timeout_add(500, self.addMessage().next)
        self.show()

    def addMessage(self):
        '''Adds a message to the graph.

        @returns: True to keep calling it, and False when all it's done.
        '''
        for mess in self.messages.get():
            if not self.alreadyStopped and not self.w3af.isRunning():
                self.alreadyStopped = True
                self._newPixel()
                self.pixelQuant = 1

            if mess is None:
                yield True
                continue
            mmseg = int(mess.getRealTime() * 1000)
            mtype = mess.getType()

            pixel = mmseg / self.timeGrouping
            # FIXME: Agrupar por tipo de mess!
            if pixel == self.countingPixel:
                self.pixelQuant += 1
            else:
                self._newPixel()
                self.countingPixel = pixel
                self.pixelQuant = 1
        yield False
        
    def _newPixel(self):
        print self.countingPixel, self.pixelQuant


class LogBody(gtk.VPaned):
    '''Body of the exploit tab.

    @param w3af: the Core instance.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(LogBody,self).__init__()
        self.w3af = w3af
        self.panels = {}

        # the paned window
        inner_hpan = gtk.HPaned()
        
        # first widget
        messag = messages.Messages()
        self.pack1(messag)

        # bottom widget
        # The log visualization
        graph = LogGraph(w3af)
        self.pack2(graph)

        self.set_position(300)
        self.show()
