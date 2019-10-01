# -*- coding: UTF-8 -*-
"""
Copyright 2015 Andres Riancho

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

from nose.plugins.attrib import attr

from w3af.core.controllers.core_helpers.fingerprint_404 import FourOhFourResponse
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.data.db.disk_deque import DiskDeque


@attr('smoke')
class TestDiskDeque(unittest.TestCase):

    def setUp(self):
        create_temp_dir()

    def test_int(self):
        disk_deque = DiskDeque(maxsize=2)

        disk_deque.append(1)
        disk_deque.append(2)

        self.assertIn(1, disk_deque)
        self.assertIn(2, disk_deque)

        disk_deque.append(3)

        self.assertNotIn(1, disk_deque)
        self.assertIn(2, disk_deque)
        self.assertIn(3, disk_deque)

    def test_len(self):
        disk_deque = DiskDeque(maxsize=2)
        self.assertEqual(len(disk_deque), 0)

        disk_deque.append(5)
        self.assertEqual(len(disk_deque), 1)

    def test_iter(self):
        disk_deque = DiskDeque(maxsize=2)
        disk_deque.append(1)
        disk_deque.append(2)

        contents = []
        for i in disk_deque:
            contents.append(i)

        self.assertEqual(contents, [1, 2])

    def test_namedtuple(self):
        disk_deque = DiskDeque(maxsize=2)

        disk_deque.append(FourOhFourResponse(clean_body='body',
                                             content_type='image',
                                             url='/'))

        for fofr in disk_deque:
            self.assertEqual(fofr.content_type, 'image')
