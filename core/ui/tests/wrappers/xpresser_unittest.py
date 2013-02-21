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

from functools import wraps
from gi.repository import Notify

from xpresser import Xpresser, ImageNotFound

from core.ui.tests.wrappers.gnome import Gnome
from core.ui.tests.wrappers.utils import (set_display_to_self,
                                          restore_original_display)

def debug_notify(meth):
    
    name = meth.__name__
    
    @wraps(meth)
    def debug(self, *args, **kwds):
        try:
            result = meth(self, *args, **kwds)
        except ImageNotFound, inf:
            title = 'Error'
            message = 'Error found while running %s%s: %s'
            message = message % (name, args, inf)
            notification = Notify.Notification.new (title, message,
                                                    'dialog-error')
            notification.show()
            raise inf
        else:
            '''
            title = 'Success'
            message = '%s(%s)' % (name, args)
            notification = Notify.Notification.new (title, message,
                                                    'dialog-information')
            notification.show()
            '''
            return result
    
    return debug



class XpresserUnittest(unittest.TestCase):
    
    GENERIC_IMAGES = os.path.join('core', 'ui', 'tests', 'gui', 'main_window', 'images')

    '''    
    @classmethod
    def setUpClass(cls):
        cls.gnome = Gnome()
        cls.gnome.start_sync()
        set_display_to_self()

    @classmethod
    def tearDownClass(cls):
        cls.gnome.stop()
        restore_original_display()
    '''
         
    def setUp(self):
        self.xp = Xpresser()
        self.xp.load_images(self.IMAGES)
        self.xp.load_images(self.GENERIC_IMAGES)
        
        Notify.init('Xpresser')
        
        self.start_gui()
        
    def start_gui(self):
        self.gui_process = subprocess.Popen(["python", "w3af_gui"],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        self.gui_process_pid = self.gui_process.pid
        
        # This is an easy way to wait for the GUI to be available before
        # starting any specific tests.
        self.xp.find('insert_target_url_here', timeout=5)
    
    def stop_gui(self):
        try:
            self.xp.find('throbber_stopped')
            self.type(['<Alt>','<F4>'], False)
            self.click('yes')
        except ImageNotFound:
            if self.gui_process_pid == self.gui_process.pid:
                self.gui_process.kill()
    
    def tearDown(self):
        self.stop_gui()
    
    @debug_notify
    def click(self, image):
        self.xp.click(image)
    
    @debug_notify
    def find(self, image, timeout=2):
        self.xp.find(image, timeout=timeout)
    
    @debug_notify
    def hover(self, *args):
        self.xp.hover(*args)
    
    @debug_notify
    def double_click(self, image):
        self.xp.double_click(image)
    
    @debug_notify
    def type(self, chars, hold):
        self.xp.type(chars, hold)
    
    def sleep(self, secs):
        time.sleep(secs)