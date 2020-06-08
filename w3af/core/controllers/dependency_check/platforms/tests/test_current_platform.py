"""
test_current_platform.py

Copyright 2014 Andres Riancho

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

from ..current_platform import get_current_platform
from ..default import DefaultPlatform
from ..base_platform import Platform


class TestCurrentPlatform(unittest.TestCase):
    def test_get_current_platform_default(self):
        default = get_current_platform([])
        self.assertIsInstance(default, DefaultPlatform)

    def test_get_current_platform_choose_match(self):
        default = get_current_platform([ChooseMe, NotMe])
        self.assertIsInstance(default, ChooseMe)

    def test_get_current_platform_choose_match_second(self):
        default = get_current_platform([NotMe, ChooseMe])
        self.assertIsInstance(default, ChooseMe)


class ChooseMe(Platform):
    @staticmethod
    def is_current_platform():
        return True


class NotMe(Platform):
    @staticmethod
    def is_current_platform():
        return False