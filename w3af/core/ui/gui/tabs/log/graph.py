"""
graph.py

Copyright 2007 Andres Riancho

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
from __future__ import division

import gtk
import gobject
import time
import itertools

import w3af.core.data.constants.severity as severity

from w3af.core.ui.gui.output.message_consumer import MessageConsumer
from w3af.core.data.db.disk_list import DiskList
from w3af.core.controllers.exceptions import (NoSuchTableException,
                                              MalformedDBException)


# margins (they have to be > 10)
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


class LogGraph(gtk.DrawingArea, MessageConsumer):
    """Defines a log visualization widget that shows an XY plot

    :author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    """
    def __init__(self, w3af):
        gtk.DrawingArea.__init__(self)
        MessageConsumer.__init__(self)
        
        self.w3af = w3af
        
        self.pangolayout = self.create_pango_layout("")

        # store all messages to be able to redraw
        self.all_messages = DiskList(table_prefix='gui_graph')
        self._need_redraw = 0
        
        # control variables
        self.alreadyStopped = False
        self.timeGrouping = 2
        self.timeBase = int(time.time() * 1000)
        self.realLeftMargin = MIZQ
        self.gc = None
        self._redraw_gen = None

        # Go live!
        self.connect("expose-event", self.area_expose_cb)
        gobject.timeout_add(500, self.draw_handler)
        self.show()
    
    def draw_handler(self):
        """
        Draws the graph.
        """
        # gtk.MAPPED: the widget can be displayed on the screen.
        # flags: http://pygtk.org/docs/pygtk/class-gtkobject.html#method-gtkobject--flags
        if self.flags() & gtk.MAPPED:
            if self._redraw_gen is None:
                self._redraw_gen = self._redraw_all()

            reset = self._redraw_gen.next()
            if reset:
                self._redraw_gen = None
        
        return True
    
    def handle_message(self, msg):
        """Adds a message to the all_messages DiskList which is then used as
        a source for drawing the graph.

        @returns: True to keep calling it, and False when all it's done.
        """
        yield super(LogGraph, self).handle_message(msg)
        
        mmseg = int(msg.get_real_time() * 1000)
        mtype = msg.get_type()
        if mtype == 'vulnerability':
            sever = msg.get_severity()
        else:
            sever = None
        self.all_messages.append((mmseg, mtype, sever))

    def _redraw_all(self):
        """
        Redraws all the graph.

        This implements a generator which has a rather strange protocol
        implemented in "draw_handler".

            * When the generator yields True a new generator is created and we
            start calling that one, so all the code after a "yield True" is run
            won't be called

            * When the generator yields False it will be called again
        """
        if self.gc is None:
            # sorry, not exposed yet...
            yield True

        # Handle the case where the DBMS has been stopped and the tables cleared
        # https://github.com/andresriancho/w3af/issues/5107
        try:
            len_all_messages = len(self.all_messages)
        except NoSuchTableException:
            # See method comment on why we yield True
            yield True
        except MalformedDBException:
            yield True

        # do we have enough data to start?
        if len_all_messages < 2:
            yield True

        try:
            # size helpers
            pan = self.all_messages[-1][0] - self.all_messages[0][0]
        except IndexError:
            # We should rarely get here, note that in the bug report the
            # IndexError is raised in the DiskList.__getitem__ , where we're
            # getting the -1 and 0 indexes. According to len(self.all_messages)
            # those indexes exist... so... we get here on rare race conditions
            #
            # https://github.com/andresriancho/w3af/issues/4211
            yield True

        self.window.clear()
        (w, h) = self.window.get_size()

        tspan = pan / self.timeGrouping
        usableWidth = w - MDER - self.realLeftMargin

        if tspan > usableWidth:
            #
            # Note that this line was changed from the previous (buggy line):
            #       self.timeGrouping *= int(tspan / usableWidth) + 1
            #
            # Which triggers https://github.com/andresriancho/w3af/issues/488
            # The new line makes it impossible for self.timeGrouping to be zero
            #
            self.timeGrouping = self.timeGrouping * int(tspan / usableWidth) + 1
            tspan = pan / self.timeGrouping

        elif tspan < usableWidth // 2 and self.timeGrouping > 2:
            self.timeGrouping //= 2
            tspan = pan / self.timeGrouping

        # real left margin
        txts = ['', 'Vulns', 'Info', '', 'Debug']
        maxw = 0
        for txt in txts:
            self.pangolayout.set_text(txt)
            (tw, th) = self.pangolayout.get_pixel_size()
            if tw > maxw:
                maxw = tw
        # 5 for the tick, 3 separating
        lm = self.realLeftMargin = int(maxw) + MIZQ + 8

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
            (tw, th) = self.pangolayout.get_pixel_size()
            self.window.draw_layout(self.gc, posx-tw//2, h-MINF+10, self.pangolayout)
        self.pangolayout.set_text("[s]")
        (tw, th) = self.pangolayout.get_pixel_size()
        self.window.draw_layout(self.gc, w-MDER+5, h-MINF-th // 2, self.pangolayout)

        # small vertical ticks and texts
        sep = (h-MSUP-MINF) / 4
        self.posHorizItems = {}
        self.maxItemHeight = {}
        posyant = MSUP
        for i,txt in enumerate(txts):
            if not txt:
                continue
            posy = int(MSUP + i*sep)
            self.posHorizItems[txt] = posy
            self.maxItemHeight[txt] = posy - posyant - 1
            posyant = posy
            self.window.draw_line(self.gc, lm-5, posy, lm, posy)
            self.pangolayout.set_text(txt)
            tw, th = self.pangolayout.get_pixel_size()
            self.window.draw_layout(self.gc, lm-tw-8, posy-th//2, self.pangolayout)

        # draw the info
        countingPixel = 0
        pixelQuant = 0
        mesind = 0

        while True:
            for (mmseg, mtype, sever) in itertools.islice(self.all_messages,
                                                          mesind, None, None):
                mesind += 1
                pixel = (mmseg - self.timeBase) // self.timeGrouping
                posx = self.realLeftMargin + pixel

                # if out of bound, restart draw
                if posx > (w - MDER):
                    yield True

                if mtype == 'debug':
                    if pixel == countingPixel:
                        pixelQuant += 1
                    else:
                        countingPixel = pixel
                        self._drawItem_debug(posx, pixelQuant)
                        pixelQuant = 1
                elif mtype == 'information':
                    self._drawItem_info(posx)
                elif mtype == 'vulnerability':
                    self._drawItem_vuln(posx, sever)
                    
            yield False
            
    def _drawItem_debug(self, posx, quant):
        posy = self.posHorizItems["Debug"] - 1
        quant = min(quant, self.maxItemHeight["Debug"])
        self.gc.set_rgb_fg_color(colors.grey)
        self.window.draw_line(self.gc, posx, posy, posx, posy - quant)
        self.gc.set_rgb_fg_color(colors.black)

    def _drawItem_info(self, posx):
        posy = self.posHorizItems["Info"]
        self.gc.set_rgb_fg_color(colors.blue)
        self.window.draw_rectangle(self.gc, True, posx - 1, posy - 1, 2, 2)
        self.gc.set_rgb_fg_color(colors.black)

    def _drawItem_vuln(self, posx, sever):
        posy = self.posHorizItems["Vulns"]
        self.gc.set_rgb_fg_color(colors.red)
        if sever == severity.LOW:
            sever = 4
        elif sever == severity.MEDIUM:
            sever = 10
        else:
            sever = 20
        self.window.draw_rectangle(
            self.gc, True, posx - 1, posy - sever, 2, sever)
        self.gc.set_rgb_fg_color(colors.black)

    def area_expose_cb(self, area, event):
        style = self.get_style()
        self.gc = style.fg_gc[gtk.STATE_NORMAL]
        self._redraw_gen = self._redraw_all()
        return True

    def _calculateXTicks(self, width):
        """Returns the ticks X position and time."""
        step = width / 10
        for i in range(10):
            punto = int(step * i)
            label = "%.2f" % (punto * self.timeGrouping / 1000)
            yield punto, label

