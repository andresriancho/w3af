'''
test_gnome.py

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
'''
import Image
import os
import time

from nose.plugins.skip import SkipTest

from w3af import ROOT_PATH
from w3af.core.ui.tests.wrappers.gnome import Gnome
from w3af.core.ui.tests.wrappers.dogtail_unittest import DogtailUnittest
from w3af.core.ui.tests.wrappers.tests.utils import is_black_image


class TestGnome(DogtailUnittest):

    X_TEST_COMMAND = 'python %s' % os.path.join(ROOT_PATH, 'core', 'ui', 'tests',
                                                'wrappers', 'tests', 'helloworld.py')

    def __init__(self, methodName='runTest'):
        DogtailUnittest.__init__(self, methodName=methodName)

    def get_screenshot(self):
        self.assertTrue(self.gnome.is_running())

        output_file = self.gnome.get_screenshot()

        screenshot_img = Image.open(output_file)
        img_width, img_height = screenshot_img.size

        self.assertEqual(img_width, Gnome.WIDTH)
        self.assertEqual(img_height, Gnome.HEIGTH)

        # It shouldn't be black since it should have the background set by the
        # user running the test in his Gnome desktop
        self.assertFalse(is_black_image(screenshot_img))

        os.remove(output_file)

    def test_run_gedit_with_dogtail(self):
        self.assertTrue(self.gnome.is_running())

        # Start the hello world in gnome
        #run_result = self.gnome.run_x_process(self.X_TEST_COMMAND, block=False)
        #self.assertTrue(run_result)

        # Let the window appear in the xvfb, note that block is False above
        self.gnome.start_vnc_client()

        try:
            try:
                os.remove('/tmp/demo-output.txt')
            except:
                pass

            # Start gedit.
            self.dogtail.utils.run("gedit")

            # Get a handle to gedit's application object.
            gedit = self.dogtail.tree.root.application('gedit')

            # Get a handle to gedit's text object.
            # Last text object is the gedit's text field
            textbuffer = gedit.findChildren(
                self.dogtail.predicate.GenericPredicate(roleName='text'))[-1]

            # This will work only if 'File Browser panel' plugin is disabled
            #textbuffer = gedit.child(roleName = 'text')

            # Load the UTF-8 demo file.
            utfdemo = file('/tmp/demo.txt')

            # Load the UTF-8 demo file into gedit's text buffer.
            textbuffer.text = utfdemo.read()

            # Get a handle to gedit's File menu.
            filemenu = gedit.menu('File')

            # Get a handle to gedit's Save button.
            savebutton = gedit.button('Save')

            # Click the button
            savebutton.click()

            # Get a handle to gedit's Save As... dialog.
            try:
                saveas = gedit.child(roleName='file chooser')
            except self.dogtail.tree.SearchError:
                try:
                    saveas = gedit.dialog(u'Save As\u2026')
                except self.dogtail.tree.SearchError:
                    saveas = gedit.dialog('Save as...')

            # We want to save to the file name 'UTF8demo.txt'.
            saveas.child(roleName='text').text = 'demo-output.txt'

            # Save the file on the Desktop

            # Don't make the mistake of only searching by name, there are multiple
            # "Desktop" entires in the Save As dialog - you have to query for the
            # roleName too - see the on-line help for the Dogtail "tree" class for
            # details
            saveas.child('tmp', roleName='table cell').click()

            #  Click the Save button.
            saveas.button('Save').click()

            # Let's quit now.
            filemenu.click()
            filemenu.menuItem('Quit').click()
        except Exception, e:
            print e
            raise
        finally:
            self.assertTrue(os.path.exists('/tmp/demo-output.txt'))

    def logout(self):
        raise SkipTest('Remove me later.')

        self.assertTrue(self.gnome.is_running())

        self.gnome.start_vnc_client()
        time.sleep(2)

        self.logout()

        self.assertTrue(False)
