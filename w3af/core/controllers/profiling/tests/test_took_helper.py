"""
test_took_helper.py

Copyright 2018 Andres Riancho

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

from mock import patch

from w3af.core.controllers.profiling.took_helper import TookLine
from w3af.core.controllers.w3afCore import w3afCore


class TestTookHelper(unittest.TestCase):
    def test_took_simple(self):
        w3af_core = w3afCore()

        took_line = TookLine(w3af_core,
                             'plugin_name',
                             'method_name',
                             debugging_id='ML7aEYsa',
                             method_params={'test': 'yes'})

        with patch('w3af.core.controllers.profiling.took_helper.om.out') as om_mock:
            took_line.send()

            self.assertEqual(om_mock.debug.call_count, 1)
            sent_message = om_mock.debug.call_args[0][0]

            self.assertRegexpMatches(sent_message,
                                     'plugin_name.method_name\(test="yes",did="ML7aEYsa"\)'
                                     ' took .*? seconds to run \(.*? seconds / .*?% consuming CPU cycles\)')

    def test_took_with_rtt(self):
        debugging_id = 'ML7aEYsa'

        w3af_core = w3afCore()
        w3af_core.uri_opener._rtt_sum_debugging_id[debugging_id] = 1.8

        took_line = TookLine(w3af_core,
                             'plugin_name',
                             'method_name',
                             debugging_id='ML7aEYsa',
                             method_params={'test': 'yes'})

        with patch('w3af.core.controllers.profiling.took_helper.om.out') as om_mock:
            took_line.send()

            self.assertEqual(om_mock.debug.call_count, 1)
            sent_message = om_mock.debug.call_args[0][0]

            self.assertRegexpMatches(sent_message,
                                     'plugin_name.method_name\(test="yes",did="ML7aEYsa"\)'
                                     ' took .*? seconds to run \(1.80 seconds / .*?% sending HTTP requests,'
                                     ' .*? seconds / .*?% consuming CPU cycles\)')
