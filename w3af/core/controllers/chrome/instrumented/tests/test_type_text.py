"""
test_type_text.py

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
import pytest

from w3af.core.controllers.chrome.tests.helpers import ExtendedHttpRequestHandler
from w3af.core.controllers.chrome.tests.base import BaseInstrumentedUnittest


pytestmark = pytest.mark.deprecated
HELLO = 'hello world'


class TestTypeTextOnInput(BaseInstrumentedUnittest):

    def test_type_text_on_input(self):
        self._unittest_setup(TypeTextHandler)

        typed = self.ic.type_text(HELLO, '#some_input')
        self.assertTrue(typed)

        value = self.ic.js_runtime_evaluate('document.querySelectorAll("#some_input")[0].value')
        self.assertEqual(value, HELLO)


class TypeTextHandler(ExtendedHttpRequestHandler):
    RESPONSE_BODY = '''
    <form id="some_form">
        <input type="text" id="some_input">
    </form>
    '''
