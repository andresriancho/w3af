'''
bruteforcer.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

import os
import unittest

from core.controllers.misc.temp_dir import create_temp_dir
from core.controllers.bruteforce.bruteforcer import bruteforcer
from core.data.parsers.urlParser import url_object


class test_bruteforcer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = create_temp_dir()

    def test_bruteforcer_default(self):
        url = url_object('http://www.w3af.org/')
        
        bf = bruteforcer()
        bf.setURL(url)
        bf.init()
        
        expected_combinations = [
                                 ('prueba1', '123abc'),
                                 ('test', 'freedom'),
                                 ('user', 'letmein'),
                                 ('www.w3af.org', 'master'),    # URL feature
                                 ('admin', '7emp7emp'),         # l337 feature
                                 ('user1', ''),                 # No password
                                 ('user1', 'user1')             # User eq password
                                ]
        generated = []
        
        next = True
        while next:
            try:
                gen_comb = bf.getNext()
                generated.append( gen_comb )
            except:
                break

        for gen_comb in expected_combinations:
            self.assertTrue( gen_comb in generated )

    def test_bruteforcer_combo(self):

        expected_combinations = [
                                 ('test', 'unittest'),
                                 ('123', 'unittest'),
                                 ('unittest', 'w00tw00t!'),
                                 ('unittest', 'unittest') 
                                ]

        combo_filename = os.path.join(self.temp_dir, 'combo.txt' )
        combo_fd = file( combo_filename, 'w')
        
        for user, password in expected_combinations:
            combo_fd.write('%s:%s\n' % (user, password))
            
        combo_fd.close()
        
        url = url_object('http://www.w3af.org/')
        
        bf = bruteforcer()
        bf.setURL(url)
        bf.setComboFile( combo_filename )
        bf.setComboSeparator(':')
        bf.init()
        
        generated = []
        
        next = True
        while next:
            try:
                gen_comb = bf.getNext()
                generated.append( gen_comb )
            except:
                break

        for gen_comb in expected_combinations:
            self.assertTrue( gen_comb in generated )

