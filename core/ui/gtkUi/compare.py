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
print "FIXME: otro reload!"
reload(comparator)
#from core.controllers.w3afException import *

ui_menu = """
<ui>
  <toolbar name="Toolbar">
    <toolitem action="ReqHeaders"/>
    <toolitem action="ReqBody"/>
    <toolitem action="RespHeaders"/>
    <toolitem action="RespBody"/>
    <separator name="sep1"/>
    <toolitem action="ClearAll"/>
    <separator name="separator"/>
    <toolitem action="Help"/>
  </toolbar>
</ui>
"""

class Compare(entries.RememberingWindow):
    '''Compares two texts.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        super(Compare,self).__init__(w3af, "compare", "w3af - Compare")
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
        self.w3af = w3af

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
            ('ReqHeaders', gtk.STOCK_GOTO_TOP, '_Request Headers', None, 'Show/Hide the request headers', self._toggle_reqhead, True),
            ('ReqBody',    gtk.STOCK_GO_UP,    '_Request Body',    None, 'Show/Hide the request body',    self._toggle_reqbody, True),
            ('RespHeaders', gtk.STOCK_GO_DOWN,     '_Response Headers', None, 'Show/Hide the response headers', self._toggle_resphead, False),
            ('RespBody',    gtk.STOCK_GOTO_BOTTOM, '_Response Body',    None, 'Show/Hide the response body',    self._toggle_respbody, False),
        ])

        # finish the toolbar
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(ui_menu)
        toolbar = uimanager.get_widget('/Toolbar')
        separat = toolbar.get_nth_item(4)
        separat.set_draw(False)
        separat.set_expand(True)
        self.vbox.pack_start(toolbar, False)

        # the line with the "send to" buttons
        hbox = gtk.HBox()
        b = entries.SemiStockButton("", gtk.STOCK_INDEX, "Send Left Request to Manual Editor")
        b.connect("clicked", self._sendRequests, "manual", "left")
        hbox.pack_start(b, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_PROPERTIES, "Send Left Request to Fuzzy Editor")
        b.connect("clicked", self._sendRequests, "fuzzy", "right")
        hbox.pack_start(b, False, False, padding=2)

        b = entries.SemiStockButton("", gtk.STOCK_SELECT_COLOR, "Send all to Cluster Responses")
        b.connect("clicked", self._sendCluster)
        hbox.pack_end(b, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_PROPERTIES, "Send Right Request to Fuzzy Editor")
        b.connect("clicked", self._sendRequests, "manual", "left")
        hbox.pack_end(b, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_INDEX, "Send Right Request to Manual Editor")
        b.connect("clicked", self._sendRequests, "fuzzy", "right")
        hbox.pack_end(b, False, False, padding=2)
        self.vbox.pack_start(hbox, False, False, padding=10)

        # the comparator itself
        cont1 = open("core/ui/gtkUi/comparator/example1.txt").read()
        cont2 = open("core/ui/gtkUi/comparator/example2.txt").read()
        comp = comparator.FileDiff()
        comp.setLeftPane("izquierda", cont1)
        comp.setRightPane("derecha", cont2)
        self.vbox.pack_start(comp.widget)

        # the page control
        box = gtk.HBox()
        self.pagesControl = entries.PagesControl(w3af, self._pageChange)
        box.pack_start(self.pagesControl, False, False, padding=5) 
        but = gtk.Button("Delete")
        but.connect("clicked", self._delete)
        box.pack_start(but, False, False, padding=10) 
        comp.rightBaseBox.pack_start(box, True, False)

        # the send to left button
        box = gtk.HBox()
        but = gtk.Button("Set the Right text here")
        but.connect("clicked", self._rightToLeft)
        box.pack_start(but, True, False) 
        comp.leftBaseBox.pack_start(box, True, False)

        self.show_all()

    def _toggle_reqhead(self, action):
        print "FIXME", action
    def _toggle_reqbody(self, action):
        print "FIXME", action
    def _toggle_resphead(self, action):
        print "FIXME", action
    def _toggle_respbody(self, action):
        print "FIXME", action
    def _help(self, action):
        print "FIXME", action
    def _clearAll(self, action):
        print "FIXME", action
    def _sendRequests(self, widg, edittype, paneside):
        print "FIXME sendRequests", edittype, paneside
    def _sendCluster(self, widg):
        print "FIXME sendCluster"
    def _delete(self, widg):
        print "FIXME delete"
    def _rightToLeft(self, widg):
        print "FIXME rigthToLeft"
    def _pageChange(self, page):
        print "FIXME pageChange"
