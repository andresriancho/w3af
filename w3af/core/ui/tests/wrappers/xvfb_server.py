"""
xvfb_server.py

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
import subprocess
import commands
import shutil
import tempfile
import threading
import time
import shlex
import os

from w3af.core.ui.tests.wrappers.constants import DISPLAY
from w3af.core.ui.tests.wrappers.utils import restore_original_display


class XVFBServer(threading.Thread):
    """
    This class is a wrapper that helps me start/stop a Xvfb server and allows
    me to run any X client in it.

    For running LDTP tests we need to run Gnome (which actually provides the a11y
    features). Gnome is started once the Xvfb is ready and all the Gnome stuff
    is handled in gnome.py
    """
    WIDTH = 1024
    HEIGTH = 768

    REQUIRED_BINS = ['convert', 'xvnc4viewer', 'Xvfb', 'x11vnc']
    
    XVFB_BIN = '/usr/bin/Xvfb'
    START_CMD = '%s %s -screen 0 %sx%sx16 -fbdir %s' % (XVFB_BIN, DISPLAY, WIDTH,
                                                        HEIGTH, tempfile.gettempdir())

    SCREEN_XWD_FILE_0 = '%s/Xvfb_screen0' % tempfile.gettempdir()

    def __init__(self):
        super(XVFBServer, self).__init__()
        self.name = 'XVFBServer'
        self.daemon = True

        self.xvfb_process = None
        self.xvfb_start_result = None
        self.vnc_server_running = False
        
        self.verify_required_bins()
    
    def verify_required_bins(self):
        for binary in self.REQUIRED_BINS:
            status, _ = commands.getstatusoutput('which %s' % binary)
            if status != 0:
                raise RuntimeError('Missing binary requirement "%s".' % binary)

    def is_installed(self):
        status, output = commands.getstatusoutput('%s --fake' % self.XVFB_BIN)

        if status == 256 and 'use: X [:<display>] [option]' in output:
            return True

        return False

    def start_sync(self):
        """Launch the xvfb process and wait for it to start the X server

        :return: True if the server is started.
        """
        i = 0
        self.start()

        while i < 10:
            if self.xvfb_start_result is None:
                time.sleep(0.2)
                i += 1
            else:
                return self.xvfb_start_result

    def run(self):
        if self.is_installed():
            args = shlex.split(self.START_CMD)
            self.xvfb_process = subprocess.Popen(args, shell=False,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE)

            # pylint: disable=E1101
            # E1101: Instance of 'Popen' has no 'wait' member
            returncode = self.xvfb_process.wait()

            if returncode != 0:
                self.xvfb_process = None
                self.xvfb_start_result = False

            self.xvfb_start_result = True

        self.xvfb_start_result = False

    def stop(self):
        if self.is_running():
            # pylint: disable=E1101
            # E1101: Instance of 'Popen' has no 'terminate' member            
            self.xvfb_process.terminate()
            self.xvfb_process = None

        return True

    def is_running(self):
        if self.xvfb_process is not None:
            return True

        return False

    def __del__(self):
        """Just in case, restore the DISPLAY to the original value again"""
        try:
            self.stop()
            restore_original_display()
        except:
            pass

    def run_x_process(self, cmd, block=False, display=DISPLAY):
        """
        Run a new process (in most cases one that will open an X window) within
        the xvfb instance.

        :param cmd: The command to run.
        :param block: If block is True this method blocks until the command
                      finishes, if not, the method returns immediately which
                      might lead to issues because of windows not being ready
                      yet inside the xvfb and checks being run on them.
        :return: True if the process was run. Please note that the method will
                 return True for commands that do not exist, fail, etc.
        """
        if not self.is_running():
            return False

        display_cmd = 'DISPLAY=%s %s' % (display, cmd)

        if block:
            commands.getoutput(display_cmd)
        else:
            args = (display_cmd,)
            th = threading.Thread(target=commands.getoutput, args=args)
            th.daemon = True
            th.name = 'XvfbProcess'
            th.start()

        return True

    def get_screenshot(self):
        """
        Verify useful for debugging! When a test does NOT pass we can take a
        screenshot of the current virtual X environment and "attach" it to the error
        log.

        Note: This requires Xvfb to be started with -fbdir
        """
        output_fname = None

        if self.is_running():

            for xwd_file in (self.SCREEN_XWD_FILE_0, ):
                temp_file = tempfile.mkstemp(prefix='xvfb-screenshot-')[1]
                shutil.copy(xwd_file, temp_file)
                target_jpeg = temp_file + '.jpeg'
                convert_cmd = 'convert %s %s' % (temp_file, target_jpeg)
                _, _ = commands.getstatusoutput(convert_cmd)

                os.unlink(temp_file)

                output_fname = target_jpeg

        return output_fname

    def start_vnc_server(self):
        """
        Starts a VNC server that will show what's being displayed in our Xvfb
        (magic++).
        """
        if self.is_running():
            args = ('x11vnc -display %s -shared -forever' % DISPLAY,)
            th = threading.Thread(target=commands.getoutput, args=args)
            th.daemon = True
            th.name = 'VNCServer'
            th.start()
            self.vnc_server_running = True
            return True

    def start_vnc_client(self):
        """
        Requires "sudo apt-get install xvnc4viewer"
        """
        if not self.vnc_server_running:
            self.start_vnc_server()
            time.sleep(3)

        args = ('DISPLAY=:0 xvnc4viewer localhost',)
        th = threading.Thread(target=commands.getoutput, args=args)
        th.daemon = True
        th.name = 'VNCClient'
        th.start()
