"""
headers.py

Copyright 2010 Andres Riancho

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
import gtk
import gobject
import pango
from w3af.core.data.parsers.doc.http_request_parser import http_request_parser

from w3af.core.ui.gui.httpeditor import HttpEditor
from w3af.core.ui.gui.entries import RememberingVPaned

CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '


class HttpHeadersView(RememberingVPaned):
    """
    Headers + raw payload view.
    """

    def __init__(self, w3af, parentView, editable=False):
        """Make object."""
        RememberingVPaned.__init__(self, w3af, 'headers_view')
        self.id = 'HttpHeadersView'
        self.label = 'Headers'
        self.startLine = ''
        self.parentView = parentView
        self.is_request = True
        box = gtk.HBox()
        self._header_store = gtk.ListStore(gobject.TYPE_STRING,
                                           gobject.TYPE_STRING)
        self._headersTreeview = gtk.TreeView(self._header_store)
        # Column for Name
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', editable)
        renderer.connect('edited', self._header_name_edited, self._header_store)
        column = gtk.TreeViewColumn(_('Name'), renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        self._headersTreeview.append_column(column)
        # Column for Value
        renderer = gtk.CellRendererText()
        renderer.set_property('editable', editable)
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        renderer.connect('edited', self._header_value_edited, self._header_store)
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
            (gtk.STOCK_GO_UP, self._move_header_up),
            (gtk.STOCK_GO_DOWN, self._move_header_down),
            (gtk.STOCK_ADD, self._add_header),
            (gtk.STOCK_DELETE, self._delete_header)
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

    def _add_header(self, widget):
        """Add header to headers."""
        i = self._header_store.append(['', ''])
        selection = self._headersTreeview.get_selection()
        selection.select_iter(i)

    def _delete_header(self, widget):
        """Delete selected header."""
        selection = self._headersTreeview.get_selection()
        (model, selected) = selection.get_selected()
        if selected:
            model.remove(selected)
        self._changed()

    def _move_header_down(self, widget):
        """Move down selected header."""
        selection = self._headersTreeview.get_selection()
        (model, selected) = selection.get_selected()
        if not selected:
            return
        next = model.iter_next(selected)
        if next:
            model.swap(selected, next)
        self._changed()

    def _move_header_up(self, widget):
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

    def _header_name_edited(self, cell, path, new_text, model):
        """Callback for header's name edited signal."""
        model[path][0] = new_text
        self._changed()

    def _header_value_edited(self, cell, path, new_text, model):
        """Callback for header's value edited signal."""
        model[path][1] = new_text
        self._changed()

    def _update_headers_tab(self, headers):
        """Update current headers view part from headers list."""
        self._header_store.clear()
        for header in headers:
            self._header_store.append([header, headers[header]])

    def _changed(self, widg=None):
        """Synchronize changes with other views (callback)."""
        if not self.initial:
            self.parentView.set_object(self.get_object())
            self.parentView.synchronize(self.id)

    def clear(self):
        """Clear view."""
        self._header_store.clear()
        self._raw.clear()
        self.startLine = ''

    def highlight(self, text, tag):
        """Highlight word in the text."""
        self._raw.highlight(text, tag)

    def show_object(self, obj):
        """Show object in view."""
        if self.is_request:
            self.startLine = obj.get_request_line()
            self._update_headers_tab(obj.get_headers())
            data = ''
            if obj.get_data():
                data = str(obj.get_data())
            self._raw.set_text(data)
        else:
            self.startLine = obj.get_status_line()
            self._update_headers_tab(obj.get_headers())
            self._raw.set_text(obj.get_body())

    def get_object(self):
        """Return object (request or response)."""
        head = self.startLine

        for header in self._header_store:
            head += header[0] + ':' + header[1] + CRLF

        if self.is_request:
            return http_request_parser(head, self._raw.get_text())
        else:
            raise Exception('HttpResponseParser is not implemented')
