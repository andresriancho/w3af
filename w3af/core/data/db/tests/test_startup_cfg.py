"""
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
import os
import unittest

from datetime import date, timedelta
from mock import Mock

from w3af.core.data.db.startup_cfg import StartUpConfig
from w3af.core.controllers.misc.home_dir import get_home_dir


class TestStartUpConfig(unittest.TestCase):

    CFG_FILE = os.path.join(get_home_dir(), 'unittest-startup.conf')

    def tearDown(self):
        try:
            os.unlink(self.CFG_FILE)
        except:
            pass

    def test_save(self):
        scfg = StartUpConfig(self.CFG_FILE)

        scfg.last_upd = date.today()
        scfg.accepted_disclaimer = True
        scfg.last_commit_id = '3f4808082c1943f964669af1a1c94245bab09c61'
        scfg.save()

    def test_load_not_exist(self):
        """
        This is a test to verify that the defaults are loaded when the file does not
        exist.
        """
        scfg = StartUpConfig('foo.conf')

        self.assertEqual(scfg.last_upd, date.today() - timedelta(days=31))
        self.assertEqual(scfg.accepted_disclaimer, False)
        self.assertEqual(scfg.last_commit_id, '')
        self.assertEqual(scfg.freq, 'D')

    def test_load_file_exists(self):
        """This is a test to verify that the things we saved were persited in
        the actual file.
        """
        # Save
        scfg = StartUpConfig(self.CFG_FILE)
        scfg.last_upd = date.today()
        scfg.accepted_disclaimer = True
        scfg.last_commit_id = '3f4808082c1943f964669af1a1c94245bab09c61'
        scfg.save()

        # Load
        scfg = StartUpConfig(self.CFG_FILE)
        self.assertEqual(scfg.last_upd, date.today())
        self.assertEqual(scfg.accepted_disclaimer, True)
        self.assertEqual(scfg.last_commit_id, '3f4808082c1943f964669af1a1c94245bab09c61')
        self.assertEqual(scfg.freq, 'D')
