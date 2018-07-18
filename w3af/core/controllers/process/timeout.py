"""
timeout.py

Copyright 2018 Andres Riancho

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
import threading
import subprocess
import traceback


class SubProcessWithTimeout(object):
    """
    Enables to run subprocess commands in a different thread with a timeout option
    """
    def __init__(self, command):
        if not isinstance(command, list):
            raise Exception('The command needs to be a list')
        self.command = command

        self.stdout = None
        self.stderr = None

        self.process = None
        self.returncode = None

    def run(self, timeout=None, **kwargs):
        """
        Run the command with a timeout
        :return: (status, output, error)
        """
        def target():
            try:
                self.process = subprocess.Popen(self.command,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                self.stdout, self.stderr = self.process.communicate()
                self.returncode = self.process.returncode
            except Exception, e:
                self.error = traceback.format_exc()
                self.returncode = -1
                self.exception = e

        # thread
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            if self.process is not None:
                self.process.terminate()

            # The timeout here gives the subprocess time to finish, and
            # protects me from race conditions in thread.is_alive() which might
            # lead to an endless loop waiting for a thread that already finished
            # to join().
            thread.join(timeout=1)

        return self.returncode, self.stdout, self.stderr
