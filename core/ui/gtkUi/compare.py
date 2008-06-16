'''
compare.py

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


import pygtk, gtk
from . import reqResViewer, entries, craftedRequests
from .comparator import comparator
from .clusterView import clusterCellWindow
import os

ui_menu = """
<ui>
  <toolbar name="Toolbar">
    <toolitem action="ReqHeaders"/>
    <toolitem action="ReqBody"/>
    <toolitem action="RespHeaders"/>
    <toolitem action="RespBody"/>
    <separator name="sep1"/>
    <toolitem action="ClearAll"/>
    <separator name="sep2"/>
    <toolitem action="Help"/>
  </toolbar>
</ui>
"""

class Compare(entries.RememberingWindow):
    '''Compares two texts.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, commHandler):
        entries.RememberingWindow.__init__(self, w3af, "compare", "w3af - Compare",
                                           onDestroy=commHandler.destroy)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
        self.w3af = w3af
        self.commHandler = commHandler
        commHandler.enable(self, self.addElement)

        # toolbar elements
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManager')
        actiongroup.add_actions([
            ('Help', gtk.STOCK_HELP, '_Help', None, 'Help regarding this window', self._help),
            ('ClearAll', gtk.STOCK_CLEAR, '_Clear All', None, 'Clear all the texts', self._clearAll),
        ])
        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('ReqHeaders', gtk.STOCK_GOTO_TOP, '_Request Headers', None, 'Show/Hide the request headers', self._toggle_reqhead, False),
            ('ReqBody',    gtk.STOCK_GO_UP,    '_Request Body',    None, 'Show/Hide the request body',    self._toggle_reqbody, False),
            ('RespHeaders', gtk.STOCK_GO_DOWN,     '_Response Headers', None, 'Show/Hide the response headers', self._toggle_resphead, True),
            ('RespBody',    gtk.STOCK_GOTO_BOTTOM, '_Response Body',    None, 'Show/Hide the response body',    self._toggle_respbody, True),
        ])

        # finish the toolbar
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(ui_menu)
        toolbar = uimanager.get_widget('/Toolbar')
        assert toolbar.get_n_items() == 8
        separat = toolbar.get_nth_item(6)
        separat.set_draw(False)
        separat.set_expand(True)
        self.vbox.pack_start(toolbar, False)
        self.tbarwidgets = [toolbar.get_nth_item(i) for i in range(6)]

        # the line with the "send to" buttons
        self.sendto_box = hbox = gtk.HBox()
        b = entries.SemiStockButton("", gtk.STOCK_INDEX, "Send Left Request to Manual Editor")
        b.connect("clicked", self._sendRequests, "manual", "left")
        hbox.pack_start(b, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_PROPERTIES, "Send Left Request to Fuzzy Editor")
        b.connect("clicked", self._sendRequests, "fuzzy", "left")
        hbox.pack_start(b, False, False, padding=2)

        image = gtk.Image()
        image.set_from_file( os.path.join( os.path.split(__file__)[0] ,'data','cluster_data.png'))
        image.show()
        self.clusterbut = gtk.Button("")
        self.clusterbut.set_tooltip_text("Send all to Cluster Responses")
        self.clusterbut.set_image(image)
        self.clusterbut.connect("clicked", self._sendCluster)
        self.clusterbut.set_sensitive(False)
        hbox.pack_end(self.clusterbut, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_PROPERTIES, "Send Right Request to Fuzzy Editor")
        b.connect("clicked", self._sendRequests, "fuzzy", "right")
        hbox.pack_end(b, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_INDEX, "Send Right Request to Manual Editor")
        b.connect("clicked", self._sendRequests, "manual", "right")
        hbox.pack_end(b, False, False, padding=2)
        self.vbox.pack_start(hbox, False, False, padding=10)

        # the comparator itself
        self.comp = comparator.FileDiff()
        self.vbox.pack_start(self.comp.widget)

        # the page control
        box = gtk.HBox()
        self.pagesControl = entries.PagesControl(w3af, self._pageChange)
        box.pack_start(self.pagesControl, False, False, padding=5) 
        self.delbut = gtk.Button("Delete")
        self.delbut.connect("clicked", self._delete)
        self.delbut.set_sensitive(False)
        box.pack_start(self.delbut, False, False, padding=10) 
        self.comp.rightBaseBox.pack_start(box, True, False)

        # the send to left button
        box = gtk.HBox()
        but = gtk.Button("Set the Right text here")
        but.connect("clicked", self._rightToLeft)
        box.pack_start(but, True, False) 
        self.comp.leftBaseBox.pack_start(box, True, False)

        # this four bool list indicates which texts to show
        self.showText = [False, False, True, True]

        # other attributes
        self.elements = []
        self.showingPage = None
        self.leftElement = None
        self.sensitiveAll(False)
        self.show_all()

    def sensitiveAll(self, how):
        '''Sets the sensitivity of almost everything.

        @param how: how to set it.
        '''
        self.comp.set_sensitive(how)
        for widg in self.tbarwidgets:
            widg.set_sensitive(how)
        self.sendto_box.set_sensitive(how)
        
    def addElement(self, element):
        '''Adds an element to the comparison.

        @param element: the element to add.
        '''
        self.elements.append(element)
        newlen = len(self.elements)
        self.showingPage = newlen-1
        realtext = self._getElementText()

        # acciones especiales
        if newlen == 1:
            # first one, turn everything on and put the text also in the left
            self.sensitiveAll(True)
            self.comp.setLeftPane("", realtext)
            self.leftElement = element
        else:
            # more than one, we can delete any
            self.delbut.set_sensitive(True)

        if any(r[2] for r in self.elements):
            self.clusterbut.set_sensitive(True)

        # put the text in the right and adjust the page selector 
        self.comp.setRightPane("", realtext)
        self.pagesControl.activate(newlen)
        self.pagesControl.setPage(newlen)

    def _delete(self, widg):
        del self.elements[self.showingPage]
        newlen = len(self.elements)
        self.pagesControl.activate(newlen)
        if self.showingPage == newlen:
            self.pagesControl.setPage(newlen)
            self.showingPage = newlen - 1

        # if we have only one left, no delete is allowed
        if len(self.elements) == 1:
            self.delbut.set_sensitive(False)
            
        if not any(r[2] for r in self.elements):
            self.clusterbut.set_sensitive(False)

        realtext = self._getElementText()
        self.comp.setRightPane("", realtext)

    def _getElementText(self, element=None):
        if element is None:
            element = self.elements[self.showingPage]
        (reqhead, reqbody, httpResp) = element
        if httpResp is not None:
            resphead = httpResp.dumpResponseHead()
            respbody = httpResp.getBody()
        else:
            resphead = ""
            respbody = ""
        alltexts = (reqhead, reqbody, resphead, respbody)
        realtext = "\n".join(x for x,y in zip(alltexts, self.showText) if y) + "\n"
        return realtext

    def _rightToLeft(self, widg):
        self.leftElement = self.elements[self.showingPage]
        realtext = self._getElementText()
        self.comp.setLeftPane("", realtext)

    def _pageChange(self, page):
        self.showingPage = page
        realtext = self._getElementText()
        self.comp.setRightPane("", realtext)

    def _toggle_reqhead(self, action):
        self._toggle_show(0)
    def _toggle_reqbody(self, action):
        self._toggle_show(1)
    def _toggle_resphead(self, action):
        self._toggle_show(2)
    def _toggle_respbody(self, action):
        self._toggle_show(3)

    def _toggle_show(self, ind):
        self.showText[ind] = not self.showText[ind]
        self.comp.setLeftPane("", self._getElementText(self.leftElement))
        self.comp.setRightPane("", self._getElementText())

    def _help(self, action):
        print "FIXME: implement help!!"

    def _clearAll(self, action):
        self.elements = []
        self.comp.setLeftPane("", "")
        self.comp.setRightPane("", "")
        self.showingPage = None
        self.leftElement = None
        self.sensitiveAll(False)
        self.delbut.set_sensitive(False)
        self.clusterbut.set_sensitive(False)

    def _sendRequests(self, widg, edittype, paneside):
        func = dict(manual=craftedRequests.ManualRequests, fuzzy=craftedRequests.FuzzyRequests)[edittype]
        if paneside == "left":
            element = self.leftElement
        else:
            element = self.elements[self.showingPage]
        (reqhead, reqbody, httpResp) = element
        func(self.w3af, (reqhead, reqbody))

    def _sendCluster(self, widg):
        data = [r[2] for r in self.elements if r[2] is not None]
        clusterCellWindow(self.w3af, data=data)
