"""
test_all.py

Copyright 2006 Andres Riancho

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

from w3af.core.data.constants.browsers import INTERNET_EXPLORER_7
from w3af.core.data.constants.dbms import MYSQL
from w3af.core.data.constants.disclaimer import DISCLAIMER
from w3af.core.data.constants.ports import MAILER
from w3af.core.data.constants.response_codes import OK
from w3af.core.data.constants.severity import HIGH
from w3af.core.data.constants.ignored_params import IGNORED_PARAMETERS
from w3af.core.data.constants.file_patterns import FILE_PATTERNS
from w3af.core.data.constants.vulns import VULNS


class TestAll(unittest.TestCase):
    """
    Simple test case that imports all constant modules in order to verify that
    they do NOT have any syntax errors. Importing one of the constants will
    simply trigger the whole file to be run.
    """
    def test_all(self):
        self.assertEqual(INTERNET_EXPLORER_7, INTERNET_EXPLORER_7)
        self.assertEqual(MYSQL, MYSQL)
        self.assertEqual(DISCLAIMER, DISCLAIMER)
        self.assertEqual(MAILER, MAILER)
        self.assertEqual(OK, OK)
        self.assertEqual(HIGH, HIGH)
        self.assertEqual(IGNORED_PARAMETERS, IGNORED_PARAMETERS)
        self.assertEqual(VULNS, VULNS)

        self.assertIn('root:x:0:0:', FILE_PATTERNS)
