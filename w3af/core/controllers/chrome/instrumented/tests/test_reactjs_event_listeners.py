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

from nose.plugins.attrib import attr

from w3af.core.controllers.chrome.instrumented.tests.base import BaseEventListenerCountTest
from w3af.core.controllers.chrome.instrumented.event_listener import EventListener


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
            '.buy-btn',
            '[data-sku="8552515751438644"]',
            '[data-sku="8552515751438644"] .shelf-stopper',
            '[data-sku="8552515751438644"] .installment span',
            '[data-sku="8552515751438644"] .shelf-item__buy-btn',
            '[data-sku="8552515751438644"] .val',
            '[data-sku="8552515751438644"] .shelf-item__price',
            '[data-sku="8552515751438644"] .shelf-item__thumb',
            '[data-sku="8552515751438644"] .val span',
            '[data-sku="8552515751438644"] .installment',
        }

        found_selectors = {el.selector for el in event_listeners}

        for expected_selector in expected_selectors:
            self.assertIn(expected_selector, found_selectors)

    def test_tshirt_sizes(self):
        url = 'https://5oiu5.codesandbox.io/'

        event_listeners = self._get_event_listeners(url)

        expected_event_listeners = {
            EventListener({u'event_type': u'load',
                           u'use_capture': False,
                           u'tag_name': u'!window',
                           u'node_type': -1,
                           u'selector': u'!window',
                           u'event_source': u'add_event_listener_other'}),
            EventListener({u'event_type': u'click',
                           u'tag_name': u'label',
                           u'text_content': u'XS',
                           u'node_type': 1,
                           u'selector': u'.filters .filters-available-size:nth-child(2) label',
                           u'event_source': u'inherit_window_document'}),
            EventListener({u'event_type': u'click',
                           u'tag_name': u'input',
                           u'text_content': u'',
                           u'node_type': 1,
                           u'selector': u'.filters .filters-available-size:nth-child(4) [type]',
                           u'event_source': u'inherit_window_document'})
        }

        for expected_event_listener in expected_event_listeners:
            self.assertIn(expected_event_listener, event_listeners)

        expected_text_contents = {'XS', 'S', 'M', 'ML', 'L', 'XL', 'XXL'}
        found_text_content = {el.get('text_content') for el in event_listeners}

        for expected_text_content in expected_text_contents:
            self.assertIn(expected_text_content, found_text_content)

        should_never_be_clickable = {u'16Product(s)found.'}

        for not_clickable_text in should_never_be_clickable:
            self.assertNotIn(not_clickable_text, found_text_content)
