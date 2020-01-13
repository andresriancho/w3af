"""
test_focus_element.py

Copyright 2020 Andres Riancho

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
import os

from urlparse import urlparse

from websocket import WebSocketConnectionClosedException

from w3af import ROOT_PATH
from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.controllers.chrome.instrumented.exceptions import InstrumentedChromeException
from w3af.core.controllers.chrome.devtools import ChromeInterfaceException
from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.tests.base import BaseInstrumentedUnittest
from w3af.core.data.url.tests.helpers.ssl_daemon import SSLServer


class TestFocusElement(BaseInstrumentedUnittest):

    def test_load_focus(self):
        self._unittest_setup(FormFocusHandler)

        messages = [m.message for m in self.ic.get_console_messages()]
        self.assertNotIn('focus', messages)

        focused = self.ic.focus('#some_input')
        self.assertTrue(focused)

        messages = [m.message for m in self.ic.get_console_messages()]
        self.assertIn('focus', messages)


class FormFocusHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '''
    <form id="some_form">
        <input type="text" id="some_input">
    </form>

    <script>
        var x = document.getElementById("some_form");
        
        x.addEventListener("focus", focus_function, true);
        x.addEventListener("blur", blur_function, true);
        
        function focus_function() {
          document.getElementById("some_input").style.backgroundColor = "yellow";
          console.log("focus");
        }
        
        function blur_function() {
          document.getElementById("some_input").style.backgroundColor = "";
          console.log("blur");
        }
    </script>
    '''