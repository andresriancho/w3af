"""
test_encode_decode.py

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
import os

from w3af.core.ui.tests.gui import GUI_TEST_ROOT_PATH
from w3af.core.ui.tests.wrappers.xpresser_unittest import XpresserUnittest


class TestEncodeDecode(XpresserUnittest):
    
    IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'encode_decode', 'images')
    EXTRA_IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'tools_menu', 'images')
    
    def setUp(self):
        super(TestEncodeDecode, self).setUp()
        self.xp.load_images(self.EXTRA_IMAGES)
        
    def test_encode_url_default(self):
        self.find('all-menu')
        self.click('encode-decode-icon')
        self.find('encode-decode-window-title')

        self.type('encode-me', False)
        
        self.click('encode')
        self.find('encode_me_result')
        
        self.click('close-with-cross')

    def test_encode_md5(self):
        self.find('all-menu')
        self.click('encode-decode-icon')
        self.find('encode-decode-window-title')

        self.type('encode-me', False)
        
        self.click('drop_down')
        self.click('md5_hash')
        
        self.click('encode')
        self.find('md5_for_encode-me')
        
        self.click('close-with-cross')
    
    def test_decode_url(self):
        self.find('all-menu')
        self.click('encode-decode-icon')
        self.find('encode-decode-window-title')

        self.click('bottom_text_input')
        self.type('hola%20mundo', False)
        
        self.click('decode')
        self.find('decode_hola_mundo_result')
        
        self.click('close-with-cross')

        