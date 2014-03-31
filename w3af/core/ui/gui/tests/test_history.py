'''
test_history.py

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
'''
import unittest
import random
import string
import time
import os

from w3af.core.ui.gui.history import HistorySuggestion


class TestHistorySuggestion(unittest.TestCase):
    '''
    Test the HistorySuggestion class.
    '''
    TEST_FILE = "test_history.pickle"
    QUANT = 5000
    LENGTH = 50
    
    def tearDown(self):
        if os.access(self.TEST_FILE, os.F_OK):
            os.remove(self.TEST_FILE)

    setUp = tearDown

    def test_basic(self): 
        # Testing History with QUANT elements
        his = HistorySuggestion(self.TEST_FILE)
    
        texts = ["".join(random.choice(
            string.letters) for x in xrange(self.LENGTH)) for y in xrange(self.QUANT)]
    
        # Storing the elements
        for txt in texts:
            his.insert(txt)
        
        his.save()
        
        # Loading from disk
        his_loaded = HistorySuggestion(self.TEST_FILE)
        
        self.assertIn(texts[-1], his_loaded.get_texts())
        self.assertIn(texts[0], his_loaded.get_texts())
        