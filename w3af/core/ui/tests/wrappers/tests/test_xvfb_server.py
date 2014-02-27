"""
test_xvfb_server.py

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
import os
import time

from PIL import Image
from nose.plugins.attrib import attr
from mock import patch

from w3af import ROOT_PATH
from w3af.core.ui.tests.wrappers.xvfb_server import XVFBServer
from w3af.core.ui.tests.wrappers.tests.utils import is_black_image


class TestEnvironment(unittest.TestCase):

    X_TEST_COMMAND = 'python %s' % os.path.join(ROOT_PATH, 'core', 'ui', 'tests',
                                                'wrappers', 'tests', 'helloworld.py')

    def setUp(self):
        self.xvfb_server = XVFBServer()

    def tearDown(self):
        self.xvfb_server.stop()

    @attr('ci_fails')
    def test_verify_xvfb_installed_true(self):
        self.assertTrue(self.xvfb_server.is_installed())

    @patch('commands.getstatusoutput', return_value=(1, ''))
    @attr('ci_fails')
    def test_verify_xvfb_installed_false_1(self, *args):
        self.assertFalse(self.xvfb_server.is_installed())

    @patch('commands.getstatusoutput', return_value=(256, ''))
    @attr('ci_fails')
    def test_verify_xvfb_installed_false_2(self, *args):
        self.assertFalse(self.xvfb_server.is_installed())

    @attr('ci_fails')
    def test_stop_not_started(self):
        self.assertTrue(self.xvfb_server.stop())

    @attr('ci_fails')
    def test_not_running(self):
        self.assertFalse(self.xvfb_server.is_running())

    @attr('ci_fails')
    def test_start(self):
        self.xvfb_server.start_sync()
        self.assertTrue(self.xvfb_server.is_running())

    @attr('ci_fails')
    def test_start_start(self):
        self.xvfb_server.start_sync()
        self.assertRaises(RuntimeError, self.xvfb_server.start_sync)
        self.assertTrue(self.xvfb_server.is_running())

    @attr('ci_fails')
    def test_two_servers(self):
        xvfb_server_1 = XVFBServer()
        xvfb_server_2 = XVFBServer()

        xvfb_server_1.start_sync()
        self.assertTrue(xvfb_server_1.is_running())

        xvfb_server_2.start_sync()
        self.assertFalse(xvfb_server_2.is_running())

        xvfb_server_1.stop()

    @attr('ci_fails')
    def test_get_screenshot_not_started(self):
        output_files = self.xvfb_server.get_screenshot()
        self.assertEqual(output_files, None)

    @attr('ci_fails')
    def test_get_screenshot(self):
        self.xvfb_server.start_sync()
        self.assertTrue(self.xvfb_server.is_running(),
                        'xvfb server failed to start.')
            
        output_file = self.xvfb_server.get_screenshot()

        screenshot_img = Image.open(output_file)
        img_width, img_height = screenshot_img.size

        self.assertEqual(img_width, XVFBServer.WIDTH)
        self.assertEqual(img_height, XVFBServer.HEIGTH)
        self.assertTrue(is_black_image(screenshot_img))

        os.remove(output_file)

    @attr('ci_fails')
    def test_run_with_stopped_xvfb(self):
        run_result = self.xvfb_server.run_x_process(self.X_TEST_COMMAND)
        self.assertFalse(run_result)

    @attr('ci_fails')
    def test_run_hello_world_in_xvfb(self):
        self.xvfb_server.start_sync()
        self.assertTrue(self.xvfb_server.is_running())

        # This should be completely black
        empty_scr_0 = self.xvfb_server.get_screenshot()
        self.assertTrue(is_black_image(Image.open(empty_scr_0)))

        # Start the hello world in the xvfb
        run_result = self.xvfb_server.run_x_process(self.X_TEST_COMMAND,
                                                    block=False)
        self.assertTrue(run_result)
        # Let the window appear in the xvfb, note that block is False above
        time.sleep(1)

        # In screen 0 there should be a window, the one I started in the
        # previous step.
        screen_0 = self.xvfb_server.get_screenshot()
        self.assertFalse(is_black_image(Image.open(screen_0)))

    @attr('ci_fails')
    def test_start_vnc_server(self):
        self.xvfb_server.start_sync()
        self.xvfb_server.start_vnc_server()