"""
test_history_access.py

Copyright 2011 Andres Riancho

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.tests.core_test_suite.test_pause_stop import CountTestMixin
from w3af.core.data.db.history import HistoryItem


class TestHistoryAccess(CountTestMixin):
    """
    Test that we're able to access the HTTP request and response History after
    the scan has finished.
    
    @see: Inherit from TestW3afCorePause to get the nice setUp().
    """
    def test_history_access(self):
        self.count_plugin.loops = 1
        self.w3afcore.start()
        
        history_item = HistoryItem() 
        self.assertTrue(history_item.load(1))
        self.assertEqual(history_item.id, 1)
        self.assertEqual(history_item.get_request().get_uri().url_string,
                         get_moth_http())
        self.assertEqual(history_item.get_response().get_uri().url_string,
                         get_moth_http())
