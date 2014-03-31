"""
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
"""
import unittest

from w3af.core.data.misc.file_utils import days_since_newest_file_update
from w3af.plugins.attack.db.sqlmap_wrapper import SQLMapWrapper


class TestSQLMapUpdate(unittest.TestCase):
    """Verify that we have an updated version of sqlmap within w3af"""
    
    def test_updated(self):
        days = days_since_newest_file_update(SQLMapWrapper.SQLMAP_LOCATION)
        
        # See http://nuclearsquid.com/writings/subtree-merging-and-you/
        #     https://www.kernel.org/pub/software/scm/git/docs/howto/using-merge-subtree.html
        setup_commands = ('git remote add -f sqlmap git://github.com/sqlmapproject/sqlmap.git',
                          'git merge -s ours --no-commit sqlmap/master',
                          'git read-tree --prefix=w3af/plugins/attack/db/sqlmap/ -u sqlmap/master',
                          "git commit -m 'Merging sqlmap into our subdirectory'")
        setup_str = ''.join(['    %s\n' % scmd for scmd in setup_commands])
        
        maintain_commands = ('git pull -s subtree --squash sqlmap master',
                             'git commit w3af',
                             'git push')
        maintain_str = ''.join(['    %s\n' % mcmd for mcmd in maintain_commands])
        
        msg = ('\nYou need to update the sqlmap installation that\'s embedded with'
              ' w3af. If you run "git remote" and sqlmap appears in the output'
              ' just run:\n'
              '%s\n'
              'Worse case scenario you will have to setup the remote:\n'
              '%s')

        msg = msg % (maintain_str, setup_str)
        
        self.assertLess(days, 30, msg)
