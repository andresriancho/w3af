"""
test_gtk_output.py

Copyright 2012 Andres Riancho

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

from w3af.core.ui.gui.output.gtk_output import GtkOutput


class TestGTKOutput(unittest.TestCase):

    def setUp(self):
        self.gtk_output = GtkOutput()

    def tearDown(self):
        self.gtk_output.end()

    def test_gtk_output(self):
        messages = []
        def observer(message):
            messages.append((message.get_type(), message.get_msg()))
            
        self.gtk_output.subscribe(observer)
        
        self.gtk_output.console('1')
        self.gtk_output.information('2')
        self.gtk_output.vulnerability('3')
        self.gtk_output.debug('4')
        self.gtk_output.error('5')

        self.gtk_output.unsubscribe(observer)

        self.gtk_output.vulnerability('ignores')

        EXPECTED = set([
            ('console', '1'),
            ('information', '2'),
            ('vulnerability', '3'),
            ('debug', ''), # Note that this empty string is correct
            ('error', '5'), ]
        )

        self.assertEquals(set(messages), EXPECTED)
