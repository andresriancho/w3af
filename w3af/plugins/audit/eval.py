"""
eval.py

Copyright 2008 Viktor Gazdag & Andres Riancho

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
import re

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList


class eval(AuditPlugin):
    """
    Find insecure eval() usage.

    :author: Viktor Gazdag ( woodspeed@gmail.com )
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    PRINT_REPEATS = 5

    PRINT_STRINGS = (
        # PHP http://php.net/eval
        "echo str_repeat('%%s',%s);" % PRINT_REPEATS,
        # Perl http://perldoc.perl.org/functions/eval.html
        "print '%%s'x%s" % PRINT_REPEATS,
        # Python
        # http://docs.python.org/reference/simple_stmts.html#the-exec-statement
        "print('%%s'*%s)" % PRINT_REPEATS,
        # ASP
        "Response.Write(new String(\"%%s\",%s))" % PRINT_REPEATS,
    )

    WAIT_OBJ = (
        # PHP http://php.net/sleep
        # Perl http://perldoc.perl.org/functions/sleep.html
        ExactDelay("sleep(%s);"),
        # Python http://docs.python.org/library/time.html#time.sleep
        ExactDelay("__import__('time').sleep(%s)"),
        # It seems that ASP doesn't support sleep! A language without sleep...
        # is not a language!
        # http://classicasp.aspfaq.com/general/how-do-i-make-my-asp-page-pause-or-sleep.html
        # JSP takes the amount in miliseconds
        # http://java.sun.com/j2se/1.4.2/docs/api/java/lang/Thread.html#sleep(long)
        ExactDelay("Thread.sleep(%s);", mult=1000),
        # ASP.NET also uses miliseconds
        # http://msdn.microsoft.com/en-us/library/d00bd51t.aspx
        # Note: The Sleep in ASP.NET is uppercase
        ExactDelay("Thread.Sleep(%s);", mult=1000),
        # NodeJS eval
        ExactDelay("var cd;var d=new Date();do{cd=new Date();}while(cd-d<%s)", mult=1000)
    )

    def __init__(self):
        AuditPlugin.__init__(self)

        # Create some random strings, which the plugin will use.
        # for the fuzz_with_echo
        self._rnd = rand_alpha(5)
        self._rnd = self._rnd.lower()
        self._expected_result = self._rnd * self.PRINT_REPEATS

        # User configured parameters
        self._use_time_delay = True
        self._use_echo = True

    def audit(self, freq, orig_response):
        """
        Tests an URL for eval() user input injection vulnerabilities.
        :param freq: A FuzzableRequest
        """
        if self._use_echo:
            self._fuzz_with_echo(freq, orig_response)

        if self._use_time_delay:
            self._fuzz_with_time_delay(freq)

    def _fuzz_with_echo(self, freq, orig_response):
        """
        Tests an URL for eval() usage vulnerabilities using echo strings.
        :param freq: A FuzzableRequest
        """
        print_strings = [pstr % (self._rnd,) for pstr in self.PRINT_STRINGS]

        mutants = create_mutants(freq, print_strings, orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_echo)

    def _fuzz_with_time_delay(self, freq):
        """
        Tests an URL for eval() usage vulnerabilities using time delays.
        :param freq: A FuzzableRequest
        """
        fake_mutants = create_mutants(freq, ['', ])
        self.worker_pool.map(self._test_delay, fake_mutants)

    def _test_delay(self, mutant):
        """
        Try to delay the response and save a vulnerability if successful
        """
        if self._has_bug(mutant):
            return

        for delay_obj in self.WAIT_OBJ:

            ed_inst = ExactDelayController(mutant, delay_obj, self._uri_opener)
            success, responses = ed_inst.delay_is_controlled()

            if success:
                desc = 'eval() input injection was found at: %s'
                desc = desc % mutant.found_at()
                
                response_ids = [r.id for r in responses]
                
                v = Vuln.from_mutant('eval() input injection vulnerability',
                                     desc, severity.HIGH, response_ids,
                                     self.get_name(), mutant)

                self.kb_append_uniq(self, 'eval', v)
                break

    def _analyze_echo(self, mutant, response):
        """
        Analyze results of the _send_mutant method that was sent in the
        _fuzz_with_echo method.
        """
        eval_error_list = self._find_eval_result(response)
        for eval_error in eval_error_list:
            if not re.search(eval_error,
                             mutant.get_original_response_body(), re.I):

                desc = 'eval() input injection was found at: %s'
                desc = desc % mutant.found_at()

                v = Vuln.from_mutant('eval() input injection vulnerability',
                                     desc, severity.HIGH, response.id,
                                     self.get_name(), mutant)

                self.kb_append_uniq(self, 'eval', v)

    def _find_eval_result(self, response):
        """
        This method searches for the randomized self._rnd string in HTMLs.

        :param response: The HTTP response object
        :return: A list of error found on the page
        """
        res = []

        if self._expected_result in response.body.lower():
            msg = 'Verified eval() input injection, found the concatenated'\
                  ' random string: "%s" in the response body. The'\
                  ' vulnerability was found on response with id %s.'
            om.out.debug(msg % (self._expected_result, response.id))
            res.append(self._expected_result)

        return res

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        opt_list = OptionList()

        desc = 'Use time delay (sleep() technique)'
        _help = 'If set to True, w3af will checks insecure eval() usage by' \
                ' analyzing of time delay result of script execution.'
        opt = opt_factory('use_time_delay', self._use_time_delay,
                          desc, 'boolean', help=_help)
        opt_list.add(opt)

        desc = 'Use echo technique'
        _help = 'If set to True, w3af will checks insecure eval() usage by' \
                ' grepping result of script execution for test strings.'
        opt = opt_factory('use_echo', self._use_echo, desc,
                          'boolean', help=_help)
        opt_list.add(opt)

        return opt_list

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._use_time_delay = options_list['use_time_delay'].get_value()
        self._use_echo = options_list['use_echo'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds eval() input injection vulnerabilities. These
        vulnerabilities are found in web applications, where the developer
        passes user controlled data to the eval() function.

        To check for vulnerabilities of this kind, the plugin sends an echo
        function with two randomized strings as a parameters (echo 'abc' + 'xyz')
        and if the resulting HTML matches the string that corresponds to the
        evaluation of the expression ('abcxyz') then a vulnerability has been
        found.
        """
