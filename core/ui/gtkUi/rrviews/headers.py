"""
headers.py

Copyright 2010 Andres Riancho

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

"""
import gtk
import gobject
import pango
from core.ui.gtkUi.httpeditor import HttpEditor
from core.ui.gtkUi.entries import RememberingVPaned
from core.data.parsers.httpRequestParser import httpRequestParser

CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '

class HttpHeadersView(RememberingVPaned):
    '''Headers + raw payload view.'''
    def __init__(self, w3af, parentView, editable=False):
        '''Make object.'''
        RememberingVPaned.__init__(self, w3af, 'headers_view')
        self.id = 'HttpHeadersView'
        self.label = 'Headers'
        self.startLine = ''
        self.parentView = parentView
        self.is_request = True
        box = gtk.HBox()
        self._headersStore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self._headersTreeview = gtk.TreeView(self._headersStore)
        # Column for Name
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', editable)
        renderer.connect('edited', self._headerNameEdited, self._headersStore)
        column = gtk.TreeViewColumn(_('Name'), renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        self._headersTreeview.append_column(column)
        # Column for Value
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', editable)
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        renderer.connect('edited', self._headerValueEdited, self._headersStore)
        column = gtk.TreeViewColumn(_('Value'), renderer, text=1)
        column.set_resizable(True)
        column.set_expand(True)
        column.set_sort_column_id(1)
        self._headersTreeview.append_column(column)
        self._scrolled = gtk.ScrolledWindow()
        self._scrolled.add(self._headersTreeview)
        self._scrolled.show_all()
        box.pack_start(self._scrolled)
        # Buttons area
        buttons = [
                (gtk.STOCK_GO_UP, self._moveHeaderUp),
                (gtk.STOCK_GO_DOWN, self._moveHeaderDown),
                (gtk.STOCK_ADD, self._addHeader),
                (gtk.STOCK_DELETE, self._deleteHeader)
                ]

        buttonBox = gtk.VBox()
        for button in buttons:
            b = gtk.Button(stock=button[0])
            b.connect("clicked", button[1])
            b.show()
            buttonBox.pack_start(b, False, False)
        buttonBox.show()

        if editable:
            box.pack_start(buttonBox, False, False)
        box.show()
        self.add(box)

        self._raw = HttpEditor(w3af)
        self._raw.show()
        self._raw.set_editable(editable)
        self._raw.set_wrap(True)
        self._raw.set_highlight_syntax(False)
        self._raw.set_highlight_current_line(False)
        self.initial = False
        if editable:
            buf = self._raw.get_buffer()
            buf.connect("changed", self._changed)
        self.add(self._raw)

    def _addHeader(self, widget):
        """Add header to headers."""
        i = self._headersStore.append(["", ""])
        selection = self._headersTreeview.get_selection()
        selection.select_iter(i)

    def _deleteHeader(self, widget):
        """Delete selected header."""
        selection = self._headersTreeview.get_selection()
        (model, selected) = selection.get_selected()
        if selected:
            model.remove(selected)
        self._changed()

    def _moveHeaderDown(self, widget):
        """Move down selected header."""
        selection = self._headersTreeview.get_selection()
        (model, selected) = selection.get_selected()
        if not selected:
            return
        next = model.iter_next(selected)
        if next:
            model.swap(selected, next)
        self._changed()

    def _moveHeaderUp(self, widget):
        """Move up selected header."""
        selection = self._headersTreeview.get_selection()
        model, selected = selection.get_selected()
        if not selected:
            return
        path = model.get_path(selected)
        position = path[-1]
        if position == 0:
            return
        prev_path = list(path)[:-1]
        prev_path.append(position - 1)
        prev = model.get_iter(tuple(prev_path))
        model.swap(selected, prev)
        self._changed()

    def _headerNameEdited(self, cell, path, new_text, model):
        '''Callback for header's name edited signal.'''
        model[path][0] = new_text
        self._changed()

    def _headerValueEdited(self, cell, path, new_text, model):
        '''Callback for header's value edited signal.'''
        model[path][1] = new_text
        self._changed()

    def _updateHeadersTab(self, headers):
        '''Update current headers view part from headers list.'''
        self._headersStore.clear()
        for header in headers:
            self._headersStore.append([header, headers[header]])

    def _changed(self, widg=None):
        '''Synchronize changes with other views (callback).'''
        if not self.initial:
            self.parentView.setObject(self.getObject())
            self.parentView.synchronize(self.id)

    def clear(self):
        '''Clear view.'''
        self._headersStore.clear()
        self._raw.clear()
        self.startLine = ''
    def highlight(self, text, tag):
        '''Highlight word in thetext.'''
        self._raw.highlight(text, tag)
    def showObject(self, obj):
        '''Show object in view.'''
        if self.is_request:
            self.startLine = obj.getRequestLine()
            self._updateHeadersTab(obj.getHeaders())
            data = ''
            if obj.getData():
                data = str(obj.getData())
            self._raw.set_text(data)
        else:
            self.startLine = obj.getStatusLine()
            self._updateHeadersTab(obj.getHeaders())
            self._raw.set_text(obj.getBody())

    def getObject(self):
        '''Return object (request or resoponse).'''
        head = self.startLine;
        for header in self._headersStore:
            head += header[0] + ':' + header[1] + CRLF
        if self.is_request:
            return httpRequestParser(head, self._raw.get_text())
        else:
            raise Exception('HttpResponseParser is not implemented')
