"""
test_random_user_agent.py

Copyright 2013 Andres Riancho

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

from w3af.core.data.user_agent.random_user_agent import get_random_user_agent


class TestRandomUserAgent(unittest.TestCase):
    def test_get_random_ua(self):
        EXPECTED = ('Mozilla', 'Windows', 'MSIE', 'Opera')
        
        for _ in xrange(100):
            rnd_ua = get_random_user_agent()
            
            for estr in EXPECTED:
                if estr in rnd_ua:
                    return
                
        self.assertTrue(False, 'Failed to find %s' % (EXPECTED,))