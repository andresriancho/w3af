'''
environment.py

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
import subprocess
import commands
import shutil
import tempfile
import threading
import time
import shlex
import os

WIDTH = 1600
HEIGTH = 1200

XVFB_BIN = '/usr/bin/Xvfb'
START_XVFB = '%s :9 -screen 1 %sx%sx16 -fbdir %s'  % (XVFB_BIN, WIDTH, HEIGTH, 
                                                      tempfile.gettempdir())

SCREEN_XWD_FILE_0 = '%s/Xvfb_screen0' % tempfile.gettempdir()
SCREEN_XWD_FILE_1 = '%s/Xvfb_screen1' % tempfile.gettempdir()


class XVFBServer(threading.Thread):
    def __init__(self):
        super(XVFBServer, self).__init__()
        self.name = 'XVFBServer'
        
        self.xvfb_process = None
        self.xvfb_start_result = None
        
    def is_installed(self):
        status, output = commands.getstatusoutput('%s --fake' % XVFB_BIN)
        
        if status == 256 and 'use: X [:<display>] [option]' in output:
            return True
        
        return False
    
    def start_sync(self):
        '''Launch the xvfb process and wait for it to start the X server
        
        @return: True if the server is started.
        '''
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
            args = shlex.split(START_XVFB)
            self.xvfb_process = subprocess.Popen(args, shell=False,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE)
            
            returncode = self.xvfb_process.wait()

            if returncode != 0:
                self.xvfb_process = None
                self.xvfb_start_result = False
            
            self.xvfb_start_result = True
        
        self.xvfb_start_result = False
    
    def stop(self):
        if self.is_running():
            self.xvfb_process.terminate()
            self.xvfb_process = None
        
        return True
    
    def is_running(self):
        if self.xvfb_process is not None:
            return True
        
        return False
    
    def run_x_process(self, cmd, block=False):
        '''
        Run a new process (in most cases one that will open an X window) within
        the xvfb instance.
        
        @param cmd: The command to run.
        @param block: If block is True this method blocks until the command
                      finishes, if not, the method returns immediately which
                      might lead to issues because of windows not being ready
                      yet inside the xvfb and checks being run on them.
        @return: True if the process was run. Please note that the method will
                 return True for commands that do not exist, fail, etc.
        '''
        if not self.is_running():
            return False
        
        display_cmd = 'DISPLAY=:9 %s' % cmd
        
        if block:
            commands.getoutput(display_cmd)
        else:
            args = (display_cmd,)
            th = threading.Thread(target=commands.getoutput, args=args)
            th.start()
        
        return True
        
    
    def get_screenshot(self):
        '''
        Verify useful for debugging! When a test does NOT pass we can take a
        screenshot of the current virtual X environment and "attach" it to the error
        log.
        
        Note: This requires Xvfb to be started with -fbdir
        '''
        output = []
        
        if self.is_running():
            
            for xwd_file in (SCREEN_XWD_FILE_0, SCREEN_XWD_FILE_1):
                temp_file = tempfile.mkstemp(prefix='xvfb-screenshot-')[1]
                shutil.copy(xwd_file, temp_file)
                target_jpeg = temp_file + '.jpeg'
                convert_cmd = 'convert %s %s' % (temp_file, target_jpeg)
                _, _ = commands.getstatusoutput(convert_cmd)
                
                os.unlink(temp_file)
                
                output.append(target_jpeg)
                
        return output
