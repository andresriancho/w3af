"""
payload_generators.py

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

import gtk
import gobject


def create_generator_menu(text_view_obj):
    """
    :return: A menu item that contains the generator classes for the fuzzy request editor window.
    """
    # The main menu
    menu = gtk.Menu()

    # Number generators
    number_generator_mi = gtk.MenuItem(_("Number generator"))
    number_generator_mi.connect(
        'activate', print_generator_text, text_view_obj, number_generator())
    menu.append(number_generator_mi)

    return menu


def print_generator_text(widget, text_view_obj, generator_instance):
    """
    Print the generator name to the textview, in the position where the cursor is at.
    """
    pass


class generic_generator(object):
    def __init__(self):
        """
        Provides generic methods and attributes for generators.

        w3af generator objects are used to create a python generator for letters, numbers, and
        other interesting things. The generator class is called from the fuzzy request editor.
        """
        self._generator_name = None


class number_generator(generic_generator):

    def __init__(self):
        """
        Provides generic methods and attributes for generators.

        w3af generator objects are used to create a python generator for letters, numbers, and
        other interesting things. The generator class is called from the fuzzy request editor.
        """
        generic_generator.__init__(self)
        self._generator_name = 'number_generator'
