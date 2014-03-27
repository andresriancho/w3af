"""
test_firefox_stealer.py

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
from nose.plugins.attrib import attr
from w3af.plugins.attack.payloads.payloads.tests.payload_test_helper import PayloadTestHelper
from w3af.plugins.attack.payloads.payload_handler import exec_payload


class test_firefox_stealer(PayloadTestHelper):

    EXPECTED_RESULT = {u'/home/moth/.mozilla/firefox/xmo3gf47.moth/cert8.db': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/content-prefs.sqlite': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/cookies.sqlite': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/extensions.ini': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/formhistory.sqlite': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/key3.db': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/permissions.sqlite': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/places.sqlite': 'Yes',
                       u'/home/moth/.mozilla/firefox/xmo3gf47.moth/signons.sqlite': 'Yes'}

    @attr('ci_fails')
    def test_firefox_stealer(self):
        result = exec_payload(self.shell, 'firefox_stealer', use_api=True)
        self.assertEquals(self.EXPECTED_RESULT, result)