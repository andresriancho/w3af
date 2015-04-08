"""
read_shell.py

Copyright 2010 Andres Riancho

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
import textwrap

import w3af.core.controllers.output_manager as om

from w3af.core.data.kb.shell import Shell
from w3af.core.controllers.exceptions import OSDetectionException
from w3af.core.controllers.intrusion_tools.readMethodHelpers import read_os_detection
from w3af.plugins.attack.payloads.decorators.download_decorator import download_debug


class ReadShell(Shell):
    """
    This class represents a shell that can only read files from the remote
    system.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, vuln, uri_opener, worker_pool):
        super(ReadShell, self).__init__(vuln, uri_opener, worker_pool)

    def help(self, command):
        """
        Handle the help command.

        TODO: When is this going to be called?
        """
        if command == 'read':
            _help = """\
            read:
                The read command echoes the content of a file to the console. The
                command takes only one parameter: the full path of the file to 
                read.
            
            Examples:
                read /etc/passwd
            """
        elif command == 'download':
            _help = """\
            download:
                The download command reads a file in the remote system and saves
                it to the local filesystem.
            
            Examples:
                download /etc/passwd /tmp/passwd
            """
        else:
            _help = """\
            Available commands:
                help                            Display this information
                lsp                             List payloads
                payload <payload>               Execute "payload" and get the result
                read <file>                     Read the remote server <file> and echo to this console
                download <remote> <local>       Download <remote> file to <local> file system location
                exit                            Exit this shell session
            """
        return textwrap.dedent(_help)

    @download_debug
    def download(self, remote_filename, local_filename):
        """
        This is a wrapper around "read" that will write the results
        to a local file.

        :param remote_filename: The remote file to download.
        :param local_filename: The local file where to write the contents of
                               the remote file.
        :return: The message to show to the user.
        """
        remote_content = self.read(remote_filename)

        if not remote_content:
            return 'Remote file does not exist.'
        else:
            try:
                fh = file(local_filename, 'w')
            except:
                return 'Failed to open local file for writing.'
            else:
                fh.write(remote_content)
                fh.close()
                return 'Success.'

    def specific_user_input(self, command, parameters, return_err=True):
        """
        This is the method that is called when a user wants to execute something
        in the shell.

        It is called from shell.generic_user_input() which provides generic
        commands like "help".

        :param command: The string representing the command that the user
                        types in the shell.
        :param parameters: A list with the parameters for @command
        """
        #
        #    Read remote files
        #
        if command == 'read':
            if len(parameters) == 1:
                filename = parameters[0]
                return self.read(filename)
            else:
                return 'Only one parameter is expected. Usage examples: ' \
                       '"read /etc/passwd", "read \'/var/foo bar/spam.eggs\'"'

        #
        #    Download remote files
        #
        elif command == 'download' and len(parameters) == 2:
            remote_filename = parameters[0]
            local_filename = parameters[1]
            return self.download(remote_filename, local_filename)

        elif return_err:
            return 'Command "%s" not found. Please type "help".' % command
        
        return

    def identify_os(self):
        """
        Identify the remote operating system by reading different files from
        the OS.
        """
        try:
            self._rOS = read_os_detection(self.read)
        except OSDetectionException:
            self._rOS = 'unknown'

        # TODO: Could we determine this by calling some payloads?
        self._rSystem = 'unknown'
        self._rSystemName = 'unknown'
        self._rUser = 'file-reader'

    def end(self):
        """
        Cleanup. In this case, do nothing.
        """
        om.out.debug('Shell cleanup complete.')

    def __repr__(self):
        """
        :return: A string representation of this shell.
        """
        if not self._rOS:
            self.identify_os()

        return '<shell object (rsystem: "' + self._rOS + '")>'

    __str__ = __repr__

    def read(self, filename):
        """
        To be overridden by subclasses.
        """
        raise NotImplementedError
