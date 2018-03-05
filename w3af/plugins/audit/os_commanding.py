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
from __future__ import with_statement

import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.config as cf

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.constants.file_patterns import FILE_PATTERNS
from w3af.core.data.kb.vuln import Vuln


class os_commanding(AuditPlugin):
    """
    Find OS Commanding vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    FILE_PATTERNS = FILE_PATTERNS 
    _multi_in = MultiIn(FILE_PATTERNS)

    def __init__(self):
        AuditPlugin.__init__(self)

        #
        #   Some internal variables
        #
        self._special_chars = ['', '&&', '|', ';', '\n', '\r\n']
        self._file_compiled_regex = []

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for OS Commanding vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # We are implementing two different ways of detecting OS Commanding
        # vulnerabilities:
        #       - Time delays
        #       - Writing a known file to the HTML output
        # The basic idea is to be able to detect ANY vulnerability, so we use
        # ALL of the known techniques
        #
        # Please note that I'm running the echo ones first in order to get them
        # into the KB before the ones with time delays so that the os_commanding
        # exploit can (with a higher degree of confidence) exploit the
        # vulnerability
        #
        # This also speeds-up the detection process a little bit in the cases
        # where there IS a vulnerability present and can be found with both
        # methods.
        self._with_echo(freq, orig_response, debugging_id)
        self._with_time_delay(freq, debugging_id)

    def _with_echo(self, freq, orig_response, debugging_id):
        """
        Tests an URL for OS Commanding vulnerabilities using cat/type to write
        the content of a known file (i.e. /etc/passwd) to the HTML.

        :param freq: A FuzzableRequest
        """
        # Prepare the strings to create the mutants
        command_list = self._get_echo_commands()
        only_command_strings = [v.get_command() for v in command_list]

        # Create the mutants, notice that we use append=False (default) and
        # True to have better coverage.
        mutants = create_mutants(freq,
                                 only_command_strings,
                                 orig_resp=orig_response)
        mutants.extend(create_mutants(freq,
                                      only_command_strings,
                                      orig_resp=orig_response,
                                      append=True))

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_echo,
                                      debugging_id=debugging_id)

    def _analyze_echo(self, mutant, response):
        """
        Analyze results of the _send_mutant method that was sent in the
        _with_echo method.
        """
        #
        #   I will only report the vulnerability once.
        #
        if self._has_bug(mutant):
            return

        for file_pattern_match in self._multi_in.query(response.get_body()):

            if file_pattern_match in mutant.get_original_response_body():
                continue

            # Search for the correct command and separator
            sent_os, sent_separator = self._get_os_separator(mutant)

            desc = 'OS Commanding was found at: %s' % mutant.found_at()
            # Create the vuln obj
            v = Vuln.from_mutant('OS commanding vulnerability', desc,
                                 severity.HIGH, response.id,
                                 self.get_name(), mutant)

            v['os'] = sent_os
            v['separator'] = sent_separator
            v.add_to_highlight(file_pattern_match)

            self.kb_append_uniq(self, 'os_commanding', v)
            break

    def _get_os_separator(self, mutant):
        """
        :param mutant: The mutant that is being analyzed.
        :return: A tuple with the OS and the command separator
        that was used to generate the mutant.
        """
        os = separator = None

        # Retrieve the data I need to create the vuln and the info objects
        command_list = self._get_echo_commands()

        # TODO: Are you sure that this works as expected ?!
        for comm in command_list:
            if comm.get_command() in mutant.get_token_value():
                os = comm.get_OS()
                separator = comm.get_separator()

        return os, separator

    def _with_time_delay(self, freq, debugging_id):
        """
        Tests an URL for OS Commanding vulnerabilities using time delays.

        :param freq: A FuzzableRequest
        """
        self._send_mutants_in_threads(func=self._find_delay_in_mutant,
                                      iterable=self._generate_delay_tests(freq, debugging_id),
                                      callback=lambda x, y: None)

    def _generate_delay_tests(self, freq, debugging_id):
        fake_mutants = create_mutants(freq, ['', ])
        fake_mutants.extend(create_mutants(freq, ['', ], append=True))

        for mutant in fake_mutants:
            #
            # Don't try to find an OS commanding using a time delay method
            # if we already found it via echo
            #
            if self._has_bug(mutant):
                return

            for delay_obj in self._get_wait_commands():
                yield mutant, delay_obj, debugging_id

    def _find_delay_in_mutant(self, (mutant, delay_obj, debugging_id)):
        """
        Try to delay the response and save a vulnerability if successful

        :param mutant: The mutant to modify and test
        :param delay_obj: The delay to use
        :param debugging_id: The debugging ID for logging
        """
        if self._has_bug(mutant):
            return

        ed = ExactDelayController(mutant, delay_obj, self._uri_opener)
        ed.set_debugging_id(debugging_id)
        success, responses = ed.delay_is_controlled()

        if not success:
            return

        desc = 'OS Commanding was found at: %s' % mutant.found_at()

        v = Vuln.from_mutant('OS commanding vulnerability', desc,
                             severity.HIGH, [r.id for r in responses],
                             self.get_name(), mutant)

        v['os'] = delay_obj.get_OS()
        v['separator'] = delay_obj.get_separator()

        self.kb_append_uniq(self, 'os_commanding', v)

    def _get_echo_commands(self):
        """
        :return: This method returns a list of commands to try to execute in
                 order to print the content of a known file.
        """
        commands = []
        for special_char in self._special_chars:
            # Unix
            cmd_string = special_char + "/bin/cat /etc/passwd"
            commands.append(Command(cmd_string, 'unix', special_char))
            # Windows
            cmd_string = special_char + "type %SYSTEMROOT%\\win.ini"
            commands.append(Command(cmd_string, 'windows', special_char))

        # Execution quotes
        commands.append(Command("`/bin/cat /etc/passwd`", 'unix', '`'))
        # FoxPro uses run to run os commands. I found one of this vulns !!
        commands.append(
            Command("run type %SYSTEMROOT%\\win.ini", 'windows', 'run'))

        # Now I filter the commands based on the target_os:
        target_os = cf.cf.get('target_os').lower()
        commands = [c for c in commands if target_os in (c.get_OS(), 'unknown')]

        return commands

    def _get_wait_commands(self):
        """
        :return: This method returns a list of commands to try to execute in
                 order to introduce a time delay.
        """
        commands = []
        for special_char in self._special_chars:
            # Windows
            cmd_fmt = special_char + 'ping -n %s localhost'
            delay_cmd = PingDelay(cmd_fmt, 'windows', special_char)
            commands.append(delay_cmd)

            # Unix
            cmd_fmt = special_char + 'ping -c %s localhost'
            delay_cmd = PingDelay(cmd_fmt, 'unix', special_char)
            commands.append(delay_cmd)

            # This is needed for solaris 10
            cmd_fmt = special_char + '/usr/sbin/ping -s localhost %s'
            delay_cmd = PingDelay(cmd_fmt, 'unix', special_char)
            commands.append(delay_cmd)

        # Using execution quotes
        commands.append(PingDelay('`ping -n %s localhost`', 'windows', '`'))
        commands.append(PingDelay('`ping -c %s localhost`', 'unix', '`'))

        # FoxPro uses the "run" macro to exec os commands. I found one of this
        # vulns !!
        commands.append(
            PingDelay('run ping -n %s localhost', 'windows', 'run '))

        # Now I filter the commands based on the target_os:
        target_os = cf.cf.get('target_os').lower()
        commands = [c for c in commands if target_os in (c.get_OS(), 'unknown')]

        return commands

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will find OS commanding vulnerabilities. The detection is
        performed using two different techniques:
            - Time delays
            - Writing a known file to the HTML output

        With time delays, the plugin sends specially crafted requests that,
        if the vulnerability is present, will delay the response for 5 seconds
        (ping -c 5 localhost).

        When using the second technique, the plugin sends specially crafted
        requests that, if the vulnerability is present, will print the content
        of a known file (i.e. /etc/passwd) to the HTML output

        This plugin has a rather long list of command separators, like ";" and
        "`" to try to match all programming languages, platforms and
        installations.
        """


class Command(object):
    """
    Defines a command that is going to be sent to the remote web app.
    """
    def __init__(self, comm, os, sep):
        self._comm = comm
        self._os = os
        self._sep = sep

    def get_OS(self):
        """
        :return: The OS
        """
        return self._os

    def get_command(self):
        """
        :return: The Command to be executed
        """
        return self._comm

    def get_separator(self):
        """
        :return: The separator, could be one of ; && | etc.
        """
        return self._sep

    def __repr__(self):
        fmt = '<Command (OS: %s, Separator: "%s", Command: "%s")>'
        return fmt % (self._os, self._sep, self._comm)


class PingDelay(Command, ExactDelay):
    def __init__(self, delay_fmt, os, sep):
        Command.__init__(self, delay_fmt, os, sep)
        ExactDelay.__init__(self, delay_fmt)
        self._delay_delta = 1
