"""
raw.py

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

from core.ui.gui.httpeditor import HttpEditor
from core.data.parsers.HTTPRequestParser import HTTPRequestParser
from core.controllers.exceptions import w3afException


class HttpRawView(HttpEditor):
    '''Raw view with HTTP Editor.'''
    def __init__(self, w3af, parentView, editable=False):
        '''Make object.'''
        HttpEditor.__init__(self, w3af)
        self.id = 'HttpRawView'
        self.label = 'Raw'
        self.parentView = parentView
        self.initial = False
        self.set_editable(editable)
        if editable:
            buf = self.textView.get_buffer()
            buf.connect("changed", self._changed)

    def show_object(self, obj):
        '''Show object in textview.'''
        self.set_text(obj.dump())

    def get_object(self):
        '''Return object (request or resoponse).'''
        head, body = self.get_text(splitted=True)
        if self.is_request:
            return HTTPRequestParser(head, body)
        else:
            raise Exception('HttpResponseParser is not implemented!:(')

    def _changed(self, widg=None):
        '''Synchronize changes with other views (callback).'''
        if not self.initial:
            try:
                obj = self.get_object()
                self.reset_bg_color()
            except w3afException, ex:
                self.set_bg_color(gtk.gdk.color_parse("#FFCACA"))
                return
            self.parentView.set_object(obj)
            self.parentView.synchronize(self.id)
