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

from __future__ import division

import pygtk, gtk, gobject
import core.ui.gtkUi.messages as messages
import time


# margenes (tienen que ser > 10)
MIZQ = 20
MDER = 20
MINF = 20
MSUP = 20

class colors:
    blue = gtk.gdk.color_parse("blue")
    black = gtk.gdk.color_parse("black")
    white = gtk.gdk.color_parse("white")
    whitesmoke = gtk.gdk.color_parse("whitesmoke")

class LogGraph(gtk.DrawingArea):
    '''Defines a log visualization widget that shows an XY plot

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        self.w3af = w3af
        super(LogGraph,self).__init__()
        self.pangolayout = self.create_pango_layout("")

        # get the messages
        self.messages = messages.getQueueDiverter()
        self.all_messages = []

        # control variables
        self.countingPixel = 0
        self.alreadyStopped = False
        self.pixelQuant = 0
        self.timeGrouping = 50
        self.pixelBase = None

        # schedule the message adding, and go live!
        gobject.timeout_add(500, self.addMessage().next)
        self.connect("expose-event", self.area_expose_cb)
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

            pixel = mmseg // self.timeGrouping
            # FIXME: Agrupar por tipo de mess!
            if pixel == self.countingPixel:
                self.pixelQuant += 1
            else:
                if self.pixelBase is None:
                    self.pixelBase = pixel
                self.countingPixel = pixel
                self._newPixel()
                self.pixelQuant = 1
        yield False
        
    def _newPixel(self):
        print self.countingPixel, self.pixelQuant
        posx = MDER + (self.countingPixel - self.pixelBase)
        (w, h)  = self.window.get_size()
        self.gc.set_rgb_fg_color(colors.blue)
        self.window.draw_line(self.gc, posx, h-MINF, posx, h-MINF-self.pixelQuant)
        self.gc.set_rgb_fg_color(colors.black)
        # FIXME: darse cuenta de que hay que resizear


    def area_expose_cb(self, area, event):
        style = self.get_style()
        self.gc = style.fg_gc[gtk.STATE_NORMAL]
        (w, h)  = self.window.get_size()

        # the axis
        self.gc.set_rgb_fg_color(colors.whitesmoke)
        self.window.draw_rectangle(self.gc, True, MIZQ, MSUP, w-MDER-MIZQ, h-MINF-MSUP)
        self.gc.set_rgb_fg_color(colors.black)
        self.window.draw_line(self.gc, MIZQ, MSUP, MIZQ, h-MINF+10)
        self.window.draw_line(self.gc, MIZQ-10, h-MINF, w-MDER, h-MINF)

        # small ticks
        sep = (w-MIZQ-MDER) / 10
        for i in range(1,11):
            posx = MIZQ + i*sep
            self.window.draw_line(self.gc, posx, h-MINF+5, posx, h-MINF)

#        self._updateRealInfo()
        # FIXME: que redibuje todo el tiempo
        return True


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
