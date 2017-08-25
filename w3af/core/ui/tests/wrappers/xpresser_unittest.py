"""
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
"""
import unittest
import time
import subprocess
import os

from functools import wraps

from nose.plugins.attrib import attr

from w3af.core.ui.tests.gui import GUI_TEST_ROOT_PATH
from w3af.core.ui.tests.wrappers.gnome import Gnome
from w3af.core.ui.tests.wrappers.utils import (set_display_to_self,
                                               restore_original_display)

try:
    from gi.repository import Notify
    from xpresser import Xpresser, ImageNotFound
except ImportError:
    # I'm mostly doing this to avoid import issues like:
    #
    # When using gi.repository you must not import static modules like "gobject".
    # Please change all occurrences of "import gobject" to
    # "from gi.repository import GObject"
    #
    # In CircleCI
    Notify = None
    Xpresser = None
    ImageNotFound = None
    ImageFound = None
else:
    class ImageFound(ImageNotFound):
        pass


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
            # pylint: disable=E1101
            notification = Notify.Notification.new(title, message,
                                                   'dialog-error')
            # pylint: enable=E1101
            notification.show()
            raise inf
        else:
            """
            title = 'Success'
            message = '%s(%s)' % (name, args)
            notification = Notify.Notification.new(title, message,
                                                   'dialog-information')
            notification.show()
            """
            return result
    
    return debug


@attr('ci_fails')
class XpresserUnittest(unittest.TestCase):
    
    GENERIC_IMAGES = os.path.join(GUI_TEST_ROOT_PATH, 'main_window', 'images')
    EXTRA_IMAGES = None
    IMAGES = None
    
    """    
    @classmethod
    def setUpClass(cls):
        cls.gnome = Gnome()
        cls.gnome.start_sync()
        set_display_to_self()

    @classmethod
    def tearDownClass(cls):
        cls.gnome.stop()
        restore_original_display()
    """
         
    def setUp(self):
        self.xp = Xpresser()
        
        all_image_paths = [self.GENERIC_IMAGES, self.EXTRA_IMAGES, self.IMAGES]
        
        for image_path in all_image_paths:
            if image_path is not None:
                self.xp.load_images(image_path)
            
        Notify.init('Xpresser')
        
        self.start_gui()
        
    def start_gui(self):
        self.gui_process = subprocess.Popen(["python", "w3af_gui", "-n"],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        self.gui_process_pid = self.gui_process.pid
        
        # Move the mouse pointer somewhere where it shouldn't break any image
        # matching (screenshot with pointer vs. stored image)
        self.xp.hover(600, 600)

        # This is an easy way to wait for the GUI to be available before
        # starting any specific tests.
        self.xp.find('insert_target_url_here', timeout=5)
        self.sleep(0.5)       
    
    def process_is_alive(self):
        return self.gui_process.poll() is None
    
    def stop_gui(self):
        if self.process_is_alive():
            self.not_find('bug_detected', timeout=1)
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
    def find(self, image, timeout=5):
        self.xp.find(image, timeout=timeout)
    
    @debug_notify
    def not_find(self, image, timeout=3):
        try:
            self.xp.find(image, timeout=timeout)
        except:
            return
        else:
            raise ImageFound('%s was found and should NOT be there' % image)
        
    @debug_notify
    def hover(self, *args):
        self.xp.hover(*args)
    
    @debug_notify
    def double_click(self, image):
        self.xp.double_click(image)
    
    @debug_notify
    def right_click(self, image):
        self.xp.right_click(image)
    
    @debug_notify
    def type(self, chars, hold):
        self.xp.type(chars, hold)
    
    def sleep(self, secs):
        time.sleep(secs)