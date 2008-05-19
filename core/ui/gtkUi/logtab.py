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
import core.data.constants.severity as severity
import time


# margenes (tienen que ser > 10)
MIZQ = 20
MDER = 30
MINF = 30
MSUP = 20

class colors:
    grey = gtk.gdk.color_parse("grey")
    red = gtk.gdk.color_parse("red")
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
        self.alreadyStopped = False
        self.timeGrouping = 2
        self.timeBase = int(time.time() * 1000)
        self.realLeftMargin = MIZQ

        # schedule the message adding, and go live!
        gobject.timeout_add(500, self.addMessage().next)
        self.connect("expose-event", self.area_expose_cb)
        self.show()

    def addMessage(self):
        '''Adds a message to the graph.

        @returns: True to keep calling it, and False when all it's done.
        '''
        somethingNew = False
        for mess in self.messages.get():
            if mess is None:
                if somethingNew:
                    self._redrawAll()
                yield True
                somethingNew = False
                continue
            somethingNew = True

            mmseg = int(mess.getRealTime() * 1000)
            mtype = mess.getType()
            if mtype == "vulnerability":
                sever = mess.getSeverity()
            else:
                sever = None
            self.all_messages.append((mmseg, mtype, sever))

        
    def _redrawAll(self):
        self.window.clear()

        # let's check if resizing is needed
        (w, h)  = self.window.get_size()
        if len(self.all_messages) > 2:
            pan = self.all_messages[-1][0] - self.all_messages[0][0]
            tspan = pan / self.timeGrouping
            usableWidth = w - MDER - self.realLeftMargin
            if tspan > usableWidth:
                self.timeGrouping *= int(tspan / usableWidth) + 1
                tspan = pan / self.timeGrouping
            elif tspan < usableWidth//2 and self.timeGrouping>1:
                self.timeGrouping //= 2
                tspan = pan / self.timeGrouping

        # real left margin
        txts = ["", "Vulns", "Info", "", "Debug"]
        maxw = 0
        for txt in txts:
            self.pangolayout.set_text(txt)
            (tw,th) = self.pangolayout.get_pixel_size()
            if tw > maxw:
                maxw = tw
        lm = self.realLeftMargin = int(maxw) + MIZQ + 8  # 5 for the tick, 3 separating

        # the axis
        self.gc.set_rgb_fg_color(colors.whitesmoke)
        self.window.draw_rectangle(self.gc, True, lm, MSUP, w-MDER-lm, h-MINF-MSUP)
        self.gc.set_rgb_fg_color(colors.black)
        self.window.draw_line(self.gc, lm, MSUP, lm, h-MINF+10)
        self.window.draw_line(self.gc, lm, h-MINF, w-MDER, h-MINF)

        # small horizontal ticks
        for x,timepoint in self._calculateXTicks(w-lm-MDER):
            posx = x + lm 
            self.window.draw_line(self.gc, posx, h-MINF+5, posx, h-MINF)
            self.pangolayout.set_text(timepoint)
            (tw,th) = self.pangolayout.get_pixel_size()
            self.window.draw_layout(self.gc, posx-tw//2, h-MINF+10, self.pangolayout)
        self.pangolayout.set_text("[s]")
        (tw,th) = self.pangolayout.get_pixel_size()
        self.window.draw_layout(self.gc, w-MDER+5, h-MINF-th//2, self.pangolayout)

        # small vertical ticks and texts
        sep = (h-MSUP-MINF) / 4
        self.posHorizItems = {}
        for i,txt in enumerate(txts):
            if not txt:
                continue
            posy = int(MSUP + i*sep)
            self.posHorizItems[txt] = posy
            self.window.draw_line(self.gc, lm-5, posy, lm, posy)
            self.pangolayout.set_text(txt)
            (tw,th) = self.pangolayout.get_pixel_size()
            self.window.draw_layout(self.gc, lm-tw-8, posy-th//2, self.pangolayout)

        # draw the info
        countingPixel = 0
        pixelQuant = 0
        for (mmseg, mtype, sever) in self.all_messages:
            pixel = (mmseg - self.timeBase) // self.timeGrouping
            posx = self.realLeftMargin + pixel
            if mtype == "debug":
                if pixel == countingPixel:
                    pixelQuant += 1
                else:
                    countingPixel = pixel
                    self._drawItem(mtype, posx, pixelQuant, sever)
                    pixelQuant = 1
            elif mtype in ("vulnerability", "information"):
                self._drawItem(mtype, posx, None, sever)

    def _drawItem(self, mtype, posx, quant, sever):
        if mtype == "debug":
            posy = self.posHorizItems["Debug"] - 1
            self.gc.set_rgb_fg_color(colors.grey)
            self.window.draw_line(self.gc, posx, posy, posx, posy-quant)
        elif mtype == "information":
            posy = self.posHorizItems["Info"]
            self.gc.set_rgb_fg_color(colors.blue)
            self.window.draw_rectangle(self.gc, True, posx-1, posy-1, 2, 2)
        elif mtype == "vulnerability":
            posy = self.posHorizItems["Vulns"]
            self.gc.set_rgb_fg_color(colors.red)
            if sever == severity.LOW:
                sever = 4
            elif sever == severity.MEDIUM:
                sever = 10
            else:
                sever = 20
            self.window.draw_rectangle(self.gc, True, posx-1, posy-sever, 2, sever)
        self.gc.set_rgb_fg_color(colors.black)

    def area_expose_cb(self, area, event):
        style = self.get_style()
        self.gc = style.fg_gc[gtk.STATE_NORMAL]
        self._redrawAll()
        return True

    def _calculateXTicks(self, width):
        '''Returns the ticks X position and time.'''
        paso = width / 10
        for i in range(10):
            punto = int(paso * i)
            label = "%.2f" % (punto * self.timeGrouping / 1000)
            yield punto, label



class LogBody(gtk.VPaned):
    '''Body of the log tab.

    @param w3af: the Core instance.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(LogBody,self).__init__()
        self.w3af = w3af

        # top vpan
        top_vbox = gtk.VBox()
        
        # Content of top vbox
        self._what_is_being_run = gtk.Label()
        gobject.timeout_add(400, self._set_what_is_running )
        self._what_is_being_run.show()
        
        messag = messages.Messages()
        messag.show()
        
        # Add the widgets to the top vbox
        top_vbox.pack_start( messag, True, True )
        top_vbox.pack_start( self._what_is_being_run, False, False )
        top_vbox.show()

        # bottom widget
        # The log visualization
        graph = LogGraph(w3af)
        
        # Add to the main vpan
        self.pack1(top_vbox)
        self.pack2(graph)

        self.set_position(300)
        self.show()

    def _set_what_is_running( self ):
        '''
        @return: True so the timeout_add keeps calling it.
        '''
        coreStatus = self.w3af.getCoreStatus()
        self._what_is_being_run.set_markup( coreStatus )
        return True
        
