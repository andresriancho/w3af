'''
xpresser_unittest.py

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
import time
import subprocess
import os

from xpresser import Xpresser, ImageNotFound
 

class XpresserUnittest(unittest.TestCase):
    
    GENERIC_IMAGES = os.path.join('core', 'ui', 'tests', 'main_window', 'images')
    
    def setUp(self):
        self.xp = Xpresser()
        self.xp.load_images(self.IMAGES)
        self.xp.load_images(self.GENERIC_IMAGES)
        self.start_gui()
        
    def start_gui(self):
        self.gui_process = subprocess.Popen(["python", "w3af_gui"])
    
    def stop_gui(self):
        try:
            self.hover('main-window-title')
            self.click('main-window-cross-close')
            self.click('yes')
        except ImageNotFound:
            self.gui_process.kill()
    
    def tearDown(self):
        self.stop_gui()
    
    def click(self, image):
        self.xp.click(image)
    
    def find(self, image):
        self.xp.find(image)
    
    def hover(self, image):
        self.xp.hover(image)