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


import gtk, webbrowser
from . import entries, craftedRequests
from .comparator import comparator

# Alternative ways of seeing the data
from .clusterGraph import distance_function_selector

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
        entries.RememberingWindow.__init__(
            self, w3af, "compare", "w3af - Compare", "Comparing_HTTP_traffic",
            onDestroy=commHandler.destroy)
        self.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.png')
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


        iconfactory = gtk.IconFactory()
        iconfactory.add_default()
        def make_iconset(path):
            return gtk.IconSet(gtk.gdk.pixbuf_new_from_file(path))

        iconfactory.add('req_head', make_iconset('core/ui/gtkUi/data/request-headers.png'))
        iconfactory.add('req_body', make_iconset('core/ui/gtkUi/data/request-body.png'))
        iconfactory.add('res_head', make_iconset('core/ui/gtkUi/data/response-headers.png'))
        iconfactory.add('res_body', make_iconset('core/ui/gtkUi/data/response-body.png'))

        gtk.stock_add((
            ('req_head', "Show Request Headers", 0, gtk.gdk.keyval_from_name('1'), 'w3af'),
            ('req_body', "Show Request Body", 0, gtk.gdk.keyval_from_name('2'), 'w3af'),
            ('res_head', "Show Response Headers", 0, gtk.gdk.keyval_from_name('3'), 'w3af'),
            ('res_body', "Show Response Body", 0, gtk.gdk.keyval_from_name('4'), 'w3af'),
        ))

        actiongroup.add_toggle_actions([
            # xml_name, icon, real_menu_text, accelerator, tooltip, callback, initial_flag
            ('ReqHeaders', 'req_head', '_Request Headers', None, 'Show/Hide the request headers', self._toggle_reqhead, False),
            ('ReqBody',    'req_body',    '_Request Body',    None, 'Show/Hide the request body',    self._toggle_reqbody, False),
            ('RespHeaders', 'res_head',     '_Response Headers', None, 'Show/Hide the response headers', self._toggle_resphead, True),
            ('RespBody',    'res_body', '_Response Body',    None, 'Show/Hide the response body',    self._toggle_respbody, True),
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
        b = entries.SemiStockButton("", gtk.STOCK_INDEX, "Send the Request of the Left to Manual Editor")
        b.connect("clicked", self._sendRequests, "manual", "left")
        hbox.pack_start(b, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_PROPERTIES, "Send the Request of the Left to Fuzzy Editor")
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
        b = entries.SemiStockButton("", gtk.STOCK_PROPERTIES, "Send the Request of the Right to Fuzzy Editor")
        b.connect("clicked", self._sendRequests, "fuzzy", "right")
        hbox.pack_end(b, False, False, padding=2)
        b = entries.SemiStockButton("", gtk.STOCK_INDEX, "Send the Request of the Right to Manual Editor")
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
        but = gtk.Button("Set text to compare")
        but.set_tooltip_text("Sets the text of the right pane into the left one")
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
        title, realtext = self._getElementText()

        # acciones especiales
        if newlen == 1:
            # first one, turn everything on and put the text also in the left
            self.sensitiveAll(True)
            self.comp.setLeftPane(title, realtext)
            self.leftElement = element
        else:
            # more than one, we can delete any
            self.delbut.set_sensitive(True)

        if len([r[2] for r in self.elements if r[2] is not None]) >= 3:
            self.clusterbut.set_sensitive(True)

        # put the text in the right and adjust the page selector 
        self.comp.setRightPane(title, realtext)
        self.pagesControl.activate(newlen)
        self.pagesControl.setPage(newlen)

    def _delete(self, widg):
        '''Deletes the page from the comparator.'''
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

        title, realtext = self._getElementText()
        self.comp.setRightPane(title, realtext)

    def _getElementText(self, element=None):
        '''Returns the text of the element.'''
        if element is None:
            element = self.elements[self.showingPage]
        (reqhead, reqbody, httpResp) = element
        if httpResp is not None:
            title = "Id: %d" % httpResp.id
            resphead = httpResp.dumpResponseHead()
            respbody = httpResp.getBody()
        else:
            title = 'Error: No HTTP response was found.'
            resphead = ""
            respbody = ""
        alltexts = (reqhead, reqbody, resphead, respbody)
        realtext = "\n".join(x for x,y in zip(alltexts, self.showText) if y) + "\n"
        return title, realtext

    def _rightToLeft(self, widg):
        '''Sets the right text in the left pane for comparison.'''
        self.leftElement = self.elements[self.showingPage]
        title, realtext = self._getElementText()
        self.comp.setLeftPane(title, realtext)

    def _pageChange(self, page):
        '''Change the selected page.'''
        self.showingPage = page
        title, realtext = self._getElementText()
        self.comp.setRightPane(title, realtext)

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
        self.comp.setLeftPane(*self._getElementText(self.leftElement))
        self.comp.setRightPane(*self._getElementText())

    def _help(self, action):
        helpfile = os.path.join(os.getcwd(), "readme/EN/gtkUiHTML/gtkUiUsersGuide.html#Comparing_HTTP_traffic")
        webbrowser.open("file://" + helpfile)

    def _clearAll(self, action):
        '''Clear all the panes.'''
        self.elements = []
        self.comp.setLeftPane("", "")
        self.comp.setRightPane("", "")
        self.showingPage = None
        self.leftElement = None
        self.sensitiveAll(False)
        self.delbut.set_sensitive(False)
        self.clusterbut.set_sensitive(False)

    def _sendRequests(self, widg, edittype, paneside):
        '''Send the request to the manual or fuzzy request window.'''
        func = dict(manual=craftedRequests.ManualRequests, fuzzy=craftedRequests.FuzzyRequests)[edittype]
        if paneside == "left":
            element = self.leftElement
        else:
            element = self.elements[self.showingPage]
        (reqhead, reqbody, httpResp) = element
        func(self.w3af, (reqhead, reqbody))

    def _sendCluster(self, widg):
        '''Send the request to the cluster window.'''
        data = [r[2] for r in self.elements if r[2] is not None]
        
        if data:
            distance_function_selector(self.w3af, data)
        else:
            # Let the user know ahout the problem
            msg = "There are no HTTP responses available to cluster."
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
            opt = dlg.run()
            dlg.destroy()        
