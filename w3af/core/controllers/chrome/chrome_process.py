"""
chrome_process.py

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
import os
import re
import time
import subprocess

from w3af.core.controllers.misc.homeDir import get_home_dir
from w3af.core.controllers.dependency_check.external.chrome import get_chrome_path


class ChromeProcess(object):

    CHROME_PATH = get_chrome_path()
    DEFAULT_FLAGS = [
             '--headless',
             '--disable-gpu',
    ]

    DEVTOOLS_PORT_RE = re.compile('DevTools listening on ws://127.0.0.1:(\d*?)/devtools/')

    def __init__(self):
        self.devtools_port = 0
        self.proxy_host = None
        self.proxy_port = None
        self.data_dir = self.get_default_user_data_dir()
        self.stdout = []
        self.stderr = []

    def get_default_user_data_dir(self):
        return os.path.join(get_home_dir(), 'chrome')

    def set_devtools_port(self, devtools_port):
        """
        By default 0 is sent to the remote-debugging-port. This will start the
        browser and bind to a random unused port.

        :param devtools_port: Port number to bind to
        """
        self.devtools_port = devtools_port

    def set_proxy(self, proxy_host, proxy_port):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def get_cmd(self):
        flags = self.DEFAULT_FLAGS[:]

        flags.append('--remote-debugging-port=%s' % self.devtools_port)
        flags.append('--user-data-dir=%s' % self.data_dir)

        if self.proxy_port and self.proxy_host:
            flags.append('--proxy-server=%s:%s' % (self.proxy_host, self.proxy_port))

        flags = ' '.join(flags)

        cmd = '%s %s' % (self.CHROME_PATH, flags)
        return cmd

    def start(self):
        proc = subprocess.Popen(self.get_cmd(),
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                close_fds=True)

        while proc.returncode is None:
            proc.poll()
            stdout_data, stderr_data = proc.communicate()
            self.store_stdout(stdout_data)
            self.store_stderr(stderr_data)
            time.sleep(0.5)

    def store_stdout(self, stdout_data):
        """
        Stores stdout data, and in some cases extracts information from it.

        :param stdout_data: String we read from Chrome's stdout
        :return: None
        """
        [self.stdout.append(l) for l in stdout_data.split()]
        [self.extract_data(l) for l in stdout_data.split()]

    def store_stderr(self, stderr_data):
        """
        Stores stderr data, and in some cases extracts information from it.

        :param stdout_data: String we read from Chrome's stderr
        :return: None
        """
        [self.stderr.append(l) for l in stderr_data.split()]
        [self.extract_data(l) for l in stderr_data.split()]

    def extract_data(self, line):
        """
        Extract important data from string

        :param line: A line printed to std(out|err) by Chrome
        :return: None
        """
        self.extract_devtools_port(line)

    def extract_devtools_port(self, line):
        """
        Find lines like:

            DevTools listening on ws://127.0.0.1:36375/devtools/browser/{uuid-4}

        And extract the port. Set the port to self.devtools_port
        """
        match_object = self.DEVTOOLS_PORT_RE.search(line)
        if not match_object:
            return

        devtools_port = match_object.group(1)
        self.devtools_port = int(devtools_port)
