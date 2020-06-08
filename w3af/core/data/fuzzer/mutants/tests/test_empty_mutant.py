"""
test_empty_mutant.py

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

from w3af.core.data.fuzzer.mutants.empty_mutant import EmptyMutant
from w3af.core.data.dc.generic.nr_kv_container import NonRepeatKeyValueContainer


class TestEmptyMutant(unittest.TestCase):
    def test_create_instance(self):
        emu = EmptyMutant()

        self.assertIsInstance(emu.get_dc(), NonRepeatKeyValueContainer)