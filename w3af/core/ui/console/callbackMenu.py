"""
callbackMenu.py

Copyright 2008 Andres Riancho

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
from w3af.core.ui.console.history import history


#TODO: extract a base class from this one and menu
class callbackMenu(object):
    """
    This is a menu-wrapper which delegates the command execution
    to the callback agent.
    It provides the same interface as a menu,
    but do not require the command line to be parsed by the console
    and do not provide any autocompletion for now.
    """

    def __init__(self, name, console, w3af, parent, callback, raw=True):
        self._name = name
        self._parent = parent
        self._callback = callback
        self._history = history()
        self._raw = raw

    def is_raw(self=None):
        #TODO: pull up
        return self._raw

    def get_history(self):
        #TODO: pull up
        return self._history

    def execute(self, line):
        return self._callback(line)

    def get_path(self):
        #TODO: pull up
        p = self._parent and self._parent.get_path() + '/' or ''
        return p + self._name
