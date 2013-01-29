'''
test_sqlmap_update.py

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
'''
import unittest

from core.data.misc.file_utils import days_since_newest_file_update
from plugins.attack.db.sqlmap_wrapper import SQLMapWrapper


class TestSQLMapUpdate(unittest.TestCase):
    '''Verify that we have an updated version of sqlmap within w3af'''
    
    def test_updated(self):
        days = days_since_newest_file_update(SQLMapWrapper.SQLMAP_LOCATION)
        
        msg = 'You need to update the sqlmap installation that\'s embedded with'\
              ' w3af, to do so please run these commands:\n'\
              'cd plugins/attack/db/sqlmap/\n'\
              'git pull\n'
        self.assertLess(days, 30, msg)
        