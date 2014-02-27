"""
test_multiple_instances.py

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
import unittest

from nose.plugins.attrib import attr

from w3af.core.controllers.w3afCore import w3afCore


@attr('smoke')
class TestW3afCore(unittest.TestCase):

    def test_multiple_instances(self):
        """Just making sure nothing crashes if I have more than 1 instance
        of w3afCore"""
        instances = []
        for _ in xrange(5):
            instances.append(w3afCore())