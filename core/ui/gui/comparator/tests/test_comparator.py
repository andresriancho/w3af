"""
test_comparator.py

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
import unittest
import gtk
import os

from core.ui.gui.comparator import comparator
from core.ui.gui.tests.mocked.utils import refresh_gui

COMPARATOR_PATH = os.path.join('core', 'ui', 'gui', 'comparator')
comparator._pixmap_path = os.path.join(COMPARATOR_PATH, 'pixmaps')


class TestComparator(unittest.TestCase):

    def test_basic(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", gtk.main_quit)
        self.window.resize(800, 400)

        doc = comparator.FileDiff()

        #cont0 = open(os.path.join(COMPARATOR_PATH, 'tests', 'example1.txt')).read()
        #cont1 = open(os.path.join(COMPARATOR_PATH, 'tests', 'example2.txt')).read()

        cont0 = 'abc\ndef\nfoo\nbar'
        cont1 = 'abc\nfoo\nbar'

        doc.set_left_pane("Test0", cont0)
        doc.set_right_pane("Test1", cont1)

        self.window.add(doc.widget)
        self.window.show()

        buf = doc.textview0.get_buffer()
        textview_0_content = buf.get_text(*buf.get_bounds())

        buf = doc.textview1.get_buffer()
        textview_1_content = buf.get_text(*buf.get_bounds())

        self.assertEqual(cont0, textview_0_content)
        self.assertEqual(cont1, textview_1_content)

        refresh_gui()
        #gtk.main()
