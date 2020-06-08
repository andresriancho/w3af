"""
test_return_args.py

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

from w3af.core.controllers.threads.threadpool import return_args


class TestReturnArgs(unittest.TestCase):

    def test_basic(self):
        args_int = return_args(int)
        self.assertEqual((('3',), 3), args_int('3'))

    def test_two_params(self):
        args_replace = return_args('foo123bar'.replace)
        self.assertEqual((('123', ''), 'foobar'), args_replace('123', ''))

    def test_kwds(self):
        args_int_two = return_args(int, base=2)
        self.assertEqual((('1',), 1), args_int_two('1'))
