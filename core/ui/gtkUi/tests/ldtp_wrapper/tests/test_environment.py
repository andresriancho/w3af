'''
test_environment.py

Copyright 2011 Andres Riancho

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
import unittest
import Image
import os
import time

from mock import patch

from core.ui.gtkUi.tests.ldtp_wrapper.environment import XVFBServer, HEIGTH, WIDTH


class TestEnvironment(unittest.TestCase):

    X_TEST_COMMAND = 'python %s' % os.path.join('core', 'ui', 'gtkUi', 'tests',
                                                'ldtp_wrapper', 'helloworld.py')
        
    def setUp(self):
        self.xvfb_server = XVFBServer()
    
    def tearDown(self):
        self.xvfb_server.stop()
        
    def test_verify_xvfb_installed_true(self):
        self.assertTrue(self.xvfb_server.is_installed())

    @patch('commands.getstatusoutput', return_value=(1,''))
    def test_verify_xvfb_installed_false_1(self, *args):
        self.assertFalse(self.xvfb_server.is_installed())

    @patch('commands.getstatusoutput', return_value=(256,''))
    def test_verify_xvfb_installed_false_2(self, *args):
        self.assertFalse(self.xvfb_server.is_installed())
        
    def test_stop_not_started(self):
        self.assertTrue( self.xvfb_server.stop() )
        
    def test_not_running(self):
        self.assertFalse( self.xvfb_server.is_running() )
    
    def test_start(self):
        self.xvfb_server.start_sync()
        self.assertTrue(self.xvfb_server.is_running())
    
    def test_start_start(self):
        self.xvfb_server.start_sync()
        self.assertRaises(RuntimeError, self.xvfb_server.start_sync)
        self.assertTrue(self.xvfb_server.is_running())
        
    def test_two_servers(self):
        xvfb_server_1 = XVFBServer()
        xvfb_server_2 = XVFBServer()
        
        xvfb_server_1.start_sync()
        self.assertTrue(xvfb_server_1.is_running())
        
        xvfb_server_2.start_sync()
        self.assertFalse(xvfb_server_2.is_running())
        
        xvfb_server_1.stop()
    
    def test_get_screenshot_not_started(self):
        output_files = self.xvfb_server.get_screenshot()
        self.assertEqual(output_files, [])

    def test_get_screenshot(self):
        self.xvfb_server.start_sync()
        output_files = self.xvfb_server.get_screenshot()
        
        self.assertEqual( len(output_files), 2, output_files)
        
        EXPECTED_SIZES = { 0: (1280, 1024),
                           1: (WIDTH, HEIGTH), }
        
        for i, screenshot_file in enumerate(output_files):
            screenshot_img = Image.open(screenshot_file)
            img_width, img_height = screenshot_img.size
            
            e_width, e_height = EXPECTED_SIZES[i]
            
            self.assertEqual(img_width, e_width)
            self.assertEqual(img_height, e_height)
            self.assertTrue( self._is_black_image(screenshot_img))
            
            os.unlink(screenshot_file)
    
    def _is_black_image(self, img_inst):
        '''@return: True if the image is completely black'''
        img_width, img_height = img_inst.size
        
        for x in xrange(img_width):
            for y in xrange(img_height):
                # 0 means black color
                if img_inst.getpixel((x, y)) != 0:
                    return False
        
        return True
    
    def test_run_with_stopped_xvfb(self):
        run_result = self.xvfb_server.run_x_process(self.X_TEST_COMMAND)
        self.assertFalse(run_result)
    
    def test_run_hello_world_in_xvfb(self):
        self.xvfb_server.start_sync()
        
        # These two should be completely black
        empty_scr_0, empty_scr_1 = self.xvfb_server.get_screenshot()
        self.assertTrue(self._is_black_image(Image.open(empty_scr_0)))
        self.assertTrue(self._is_black_image(Image.open(empty_scr_1)))
        
        # Start the hello world in the xvfb
        run_result = self.xvfb_server.run_x_process(self.X_TEST_COMMAND, block=False)
        self.assertTrue(run_result)
        # Let the window appear in the xvfb, note that block is False above
        time.sleep(1)
        
        # In screen 0 there should be a window, the one I started in the
        # previous step.
        screen_0, screen_1 = self.xvfb_server.get_screenshot()
        self.assertFalse(self._is_black_image(Image.open(screen_0)))
        self.assertTrue(self._is_black_image(Image.open(screen_1)))
        