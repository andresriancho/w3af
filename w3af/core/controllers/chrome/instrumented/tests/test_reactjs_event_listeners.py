"""
test_count_event_listeners.py

Copyright 2019 Andres Riancho

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
from __future__ import print_function

import pprint
from nose.plugins.attrib import attr

from w3af.core.controllers.chrome.instrumented.tests.base import BaseEventListenerCountTest


@attr('internet')
class TestCountEventListeners(BaseEventListenerCountTest):
    def test_button_onclick(self):
        url = 'https://84ol32ono9.codesandbox.io/'
        event_listeners = self._get_event_listeners(url)

        expected_selectors = {'!window', '!document', 'button'}
        found_selectors = {el.selector for el in event_listeners}
        self.assertEqual(found_selectors, expected_selectors)

        button_el = event_listeners[2]
        self.assertEqual(button_el.event_type, 'click')

    def test_add_to_cart(self):
        url = 'https://react-shopping-cart-67954.firebaseapp.com/'
        event_listeners = self._get_event_listeners(url)

        expected_selectors = {
            '!window',
            '!document',
            '.bag--float-cart-closed .bag__quantity',
            '.bag--float-cart-closed',
            '.buy-btn'
        }

        found_selectors = {el.selector for el in event_listeners}
        self.assertEqual(found_selectors, expected_selectors)

        self.assertEqual(event_listeners, {}, pprint.pformat(event_listeners))


