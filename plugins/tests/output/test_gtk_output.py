'''
test_gtk_output.py

Copyright 2012 Andres Riancho

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
import unittest

import core.data.kb.knowledge_base as kb

from plugins.output.gtk_output import gtk_output


class TestGTKOutput(unittest.TestCase):

    def setUp(self):
        self.plugin = gtk_output()

    def tearDown(self):
        self.plugin.end()

    def test_gtk_output(self):
        self.plugin.console('1')
        self.plugin.information('2')
        self.plugin.vulnerability('3')
        self.plugin.debug('4')
        self.plugin.error('5')

        gtk_output_queue = kb.kb.get('gtk_output', 'queue')

        EXPECTED = set([
            ('console', '1'),
            ('information', '2'),
            ('vulnerability', '3'),
            ('debug', ''), # Note that this empty string is correct
            ('error', '5'), ]
        )

        from_queue = set()
        # pylint: disable-msg=E1103
        # E1103: Instance of 'list' has no 'qsize' member (but some types
        # could not be inferred)
        while gtk_output_queue.qsize() > 0:
            msg = gtk_output_queue.get()
            from_queue.add((msg.get_type(), msg.get_msg()))

        self.assertEquals(from_queue, EXPECTED)
