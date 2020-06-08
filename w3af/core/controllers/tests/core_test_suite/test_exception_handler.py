"""
test_exception_handling.py

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
from w3af.core.controllers.tests.core_test_suite.test_pause_stop import CountTestMixin


class TestExceptionHandler(CountTestMixin):
    """
    Inherit from TestW3afCorePause to get the nice setUp().
    """
    def test_same_id(self):
        """
        Verify that the exception handler is the same before and after the scan
        """
        before_id_ehandler = id(self.w3afcore.exception_handler)
        
        self.w3afcore.start()
        
        after_id_ehandler = id(self.w3afcore.exception_handler)
        
        self.assertEqual(before_id_ehandler, after_id_ehandler)