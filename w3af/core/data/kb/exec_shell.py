"""
exec_shell.py

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

import w3af.plugins.attack.payloads.payload_handler as payload_handler
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.intrusion_tools.execMethodHelpers import os_detection_exec
from w3af.core.controllers.payload_transfer.payload_transfer_factory import payload_transfer_factory
from w3af.core.data.kb.shell import Shell
from w3af.plugins.attack.payloads.decorators.read_decorator import read_debug
from w3af.plugins.attack.payloads.decorators.download_decorator import download_debug


class ExecShell(Shell):
    """
    This class represents a shell where users can execute commands in the remote
    operating system and get the output back.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, vuln, uri_opener, worker_pool):
        Shell.__init__(self, vuln, uri_opener, worker_pool)

        # For writing files to the remote server
        self._transfer_handler = None

    def execute(self, cmd):
        raise NotImplementedError

    def help(self, command):
        """
        Handle the help command.
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
                write <file> <content>          Write <content> to the remote <file>
                upload <local> <remote>         Upload <local> file to <remote> location
                execute <cmd>                   
                exec <cmd>                      
                e <cmd>                         Run <cmd> on the remote operating system
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

    def upload(self, local_filename, remote_filename):
        """
        This is a wrapper around "write" that will upload a local file
        to the remote filesystem.

        :param local_filename: The local file to read and then upload to the
                               remote system.
        :param remote_filename: The remote file to create and write contents to.

        :return: The message to show to the user.
        """
        try:
            fh = file(local_filename, 'r')
        except:
            return 'Failed to open local file for reading.'
        else:
            file_content = fh.read()
            fh.close()
            self.write(remote_filename, file_content)
            return 'Success.'

    def write(self, remote_filename, file_content):
        """
        Write a the contents of the parameter "file_content" to the
        "remote_filename" file in the remote filesystem.

        :param remote_filename: The filename where to write the file_content
        :param file_content: The string to write in the remote file

        :return: The message to show to the user.
        """
        if not self._transfer_handler:
            # Get the fastest transfer method
            try:
                ptf = payload_transfer_factory(self.execute)
                self._transfer_handler = ptf.get_transfer_handler()
            except BaseFrameworkException, e:
                return '%s' % e

        if not self._transfer_handler.can_transfer():
            return 'Failed to transfer, the transfer handler failed.'
        else:
            msg = 'The file transfer will take %s seconds'
            handler = self._transfer_handler
            estimated_time = handler.estimate_transfer_time(len(file_content))
            om.out.debug(msg % estimated_time)

            self._transfer_handler.transfer(file_content, remote_filename)
            om.out.debug('Finished file transfer.')

            return 'File upload was successful.'

    def specific_user_input(self, command, parameters):
        """
        This is the method that is called when a user wants to execute something
        in the shell and is called from shell.generic_user_input() which
        provides generic commands like "help".

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
        #    Write remote files
        #
        elif command == 'write' and len(parameters) == 2:
            filename = parameters[0]
            content = parameters[1]
            return self.write(filename, content)

        #
        #    Upload local files to the remote system
        #
        elif command == 'upload' and len(parameters) == 2:
            remote_filename = parameters[1]
            local_filename = parameters[0]
            return self.upload(local_filename, remote_filename)

        #
        #    Commands that are common to shells that can EXECUTE commands:
        #

        #
        #    Execute the command in the remote host
        #
        elif command in ['e', 'exec', 'execute']:
            return self.execute(' '.join(parameters))

        else:
            return 'Command "%s" not found. Please type "help".' % command

    def get_unlink_command(self):
        """
        :return: The command to be used to remove files in the remote operating
                 system. Examples:
                     - rm -rf %s
                     - del %s
                 The %s will be replaced by the file to be read.
        """
        if self._rOS == 'windows':
            return 'del %s'
        else:
            return 'rm -rf %s'

    def unlink(self, filename):
        """
        :param filename: The filename to unlink from the remote filesystem.
        """
        unlink_command_format = self.get_unlink_command()
        unlink_command = unlink_command_format % (filename,)
        return self.execute(unlink_command)

    def get_read_command(self, filename):
        """
        :param filename: Need the filename to determine if we need to put quotes
                         around it (because of spaces in the filename) or not.

        :return: The command to be used to read files in the remote operating
                 system. Examples:
                     - cat %s
                     - type %s
                 The %s will be replaced by the file to be read.
        """
        if self._rOS == 'windows':
            command = 'type %s'
        else:
            command = 'cat %s'

        if ' ' in filename:
            return command.replace('%s', '"%s"')

        return command

    @read_debug
    def read(self, filename):
        """
        Read a file in the remote server by running "cat" or "type" depending
        on the identified OS.
        """
        read_command_format = self.get_read_command(filename)
        read_command = read_command_format % (filename,)
        return self.execute(read_command)

    def end_interaction(self):
        """
        When the user executes "exit" in the console, this method is called.
        Basically, here we handle WHAT TO DO in that case. In most cases (and
        this is why we implemented it this way here) the response is "yes, do it
        end me" that equals to "return True".

        In some other cases, the shell prints something to the console and then
        exists, or maybe some other, more complex, thing.
        """
        return True

    def _print_runnable_payloads(self):
        """
        Print the payloads that can be run using this exploit.

        :return: A list with all runnable payloads.
        """
        payloads = payload_handler.runnable_payloads(self)
        payloads.sort()
        return '\n'.join(payloads)

    def end(self):
        """
        This method is called when the shell is not going to be used anymore.
        It should be used to remove the auxiliary files (local and remote)
        generated by the shell.

        :return: None
        """
        pass

    def get_name(self):
        """
        This method is called when the shell is used, in order to create a
        prompt for the user.

        :return: The name of the shell ( os_commanding_shell, dav, etc )
        """
        raise NotImplementedError

    def identify_os(self):
        """
        Identify the remote operating system and get some remote variables to
        show to the user.
        """
        self._rOS = os_detection_exec(self.execute)

        if self._rOS == 'linux':
            self._rUser = self.execute('whoami').strip()
            self._rSystem = self.execute('uname -o -r -n -m -s').strip()
            self._rSystemName = self.execute('uname -n').strip()
        elif self._rOS == 'windows':
            self._rUser = self.execute('echo %USERDOMAIN%\%USERNAME%').strip()
            self._rSystem = self.execute(
                'echo %COMPUTERNAME% - %OS% - %PROCESSOR_IDENTIFIER%').strip()
            self._rSystemName = self.execute('echo %COMPUTERNAME%').strip()
        else:
            self._rUser = 'unknown'
            self._rSystem = 'unknown'
            self._rSystemName = 'unknown'

    def __repr__(self):
        if not self._rOS:
            self.identify_os()
        fmt = '<%s object (ruser: "%s" | rsystem: "%s")>'
        return fmt % (self.get_name(), self.get_remote_user(), 
                      self.get_remote_system())

    __str__ = __repr__
