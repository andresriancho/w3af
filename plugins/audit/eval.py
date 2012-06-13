'''
eval.py

Copyright 2008 Viktor Gazdag & Andres Riancho

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
import re

import core.controllers.outputManager as om
import core.data.constants.severity as severity
import core.data.kb.info as info
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.delay_detection.exact_delay import exact_delay
from core.controllers.delay_detection.delay import delay
from core.data.fuzzer.fuzzer import createMutants, createRandAlpha
from core.data.options.option import option
from core.data.options.optionList import optionList




class eval(baseAuditPlugin):
    '''
    Find insecure eval() usage.

    @author: Viktor Gazdag ( woodspeed@gmail.com ) &
        Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    PRINT_STRINGS = (
        # PHP http://php.net/eval
        "echo str_repeat('%s',5);",
        # Perl http://perldoc.perl.org/functions/eval.html
        "print '%s'x5",
        # Python http://docs.python.org/reference/simple_stmts.html#the-exec-statement
        "print '%s'*5",
        # ASP
        "Response.Write(new String(\"%s\",5))"
     )
    
    WAIT_OBJ = (
        # PHP http://php.net/sleep
        # Perl http://perldoc.perl.org/functions/sleep.html
        delay("sleep(%s);"),
        # Python http://docs.python.org/library/time.html#time.sleep
        delay("import time;time.sleep(%s);"),
        # It seems that ASP doesn't support sleep! A language without sleep...
        # is not a language!
        # http://classicasp.aspfaq.com/general/how-do-i-make-my-asp-page-pause-or-sleep.html
        # JSP takes the amount in miliseconds
        # http://java.sun.com/j2se/1.4.2/docs/api/java/lang/Thread.html#sleep(long)
        delay("Thread.sleep(%s);", mult=1000),
        # ASP.NET also uses miliseconds
        # http://msdn.microsoft.com/en-us/library/d00bd51t.aspx
        # Note: The Sleep in ASP.NET is uppercase
        delay("Thread.Sleep(%s);", mult=1000)
    )

    def __init__(self):
        baseAuditPlugin.__init__(self)

        # Create some random strings, which the plugin will use.
        # for the fuzz_with_echo
        self._rnd = createRandAlpha(5)
        
        # User configured parameters
        self._use_time_delay = True
        self._use_echo = True

    def audit(self, freq):
        '''
        Tests an URL for eval() user input injection vulnerabilities.
        @param freq: A fuzzableRequest
        '''
        om.out.debug('eval plugin is testing: ' + freq.getURL())

        if self._use_echo:
            self._fuzz_with_echo(freq)
        
        if self._use_time_delay:
            self._fuzz_with_time_delay(freq)

    def _fuzz_with_echo(self, freq):
        '''
        Tests an URL for eval() usage vulnerabilities using echo strings.
        @param freq: A fuzzableRequest
        '''
        oResponse = self._uri_opener.send_mutant(freq)
        print_strings = [pstr % (self._rnd,) for pstr in self.PRINT_STRINGS]
            
        mutants = createMutants(freq, print_strings, oResponse=oResponse)

        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._has_no_bug(mutant):
                args = (mutant,)
                kwds = {'callback': self._analyze_echo }
                self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                    kwds=kwds)                
        self._join()

    def _fuzz_with_time_delay(self, freq):
        '''
        Tests an URL for eval() usage vulnerabilities using time delays.
        @param freq: A fuzzableRequest
        '''
        fake_mutants = createMutants(freq, ['',])
        
        for mutant in fake_mutants:
            
            if self._has_bug(mutant):
                continue

            for delay_obj in self.WAIT_OBJ:
                
                ed = exact_delay(mutant, delay_obj, self._uri_opener)
                success, responses = ed.delay_is_controlled()

                if success:
                    v = vuln.vuln(mutant)
                    v.setPluginName(self.getName())
                    v.setId( [r.id for r in responses] )
                    v.setSeverity(severity.HIGH)
                    v.setName('eval() input injection vulnerability')
                    v.setDesc('eval() input injection was found at: ' + mutant.foundAt())
                    kb.kb.append(self, 'eval', v)
                    break
                        
    def _analyze_echo(self, mutant, response):
        '''
        Analyze results of the _send_mutant method that was sent in the
        _fuzz_with_echo method.
        '''
        with self._plugin_lock:
            
            #
            #   I will only report the vulnerability once.
            #
            if self._has_no_bug(mutant):
                
                eval_error_list = self._find_eval_result(response)
                for eval_error in eval_error_list:
                    if not re.search(eval_error, mutant.getOriginalResponseBody(), re.IGNORECASE):
                        v = vuln.vuln(mutant)
                        v.setPluginName(self.getName())
                        v.setId(response.id)
                        v.setSeverity(severity.HIGH)
                        v.setName('eval() input injection vulnerability')
                        v.setDesc('eval() input injection was found at: ' + mutant.foundAt())
                        kb.kb.append(self, 'eval', v)

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._join()
        self.printUniq(kb.kb.getData('eval', 'eval'), 'VAR')

    def _find_eval_result(self, response):
        '''
        This method searches for the randomized self._rnd string in html's.

        @parameter response: The HTTP response object
        @return: A list of error found on the page
        '''
        res = []
        for eval_error in self._get_eval_errors():
            match = re.search(eval_error, response.body, re.IGNORECASE)
            if match:
                msg = 'Verified eval() input injection, found the concatenated random string: "'
                msg += response.getBody()[match.start():match.end()] + '" '
                msg += 'in the response body. '
                msg += 'The vulnerability was found on response with id ' + str(response.id) + '.'
                om.out.debug(msg)
                res.append(eval_error)
        return res

    def _get_eval_errors(self):
        '''
        @return: The string that results from the evaluation of what I sent.
        '''
        return [self._rnd*5]

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        
        d = 'Use time delay (sleep() technique)'
        h = 'If set to True, w3af will checks insecure eval() usage by analyzing'
        h += ' of time delay result of script execution.'
        o = option('useTimeDelay', self._use_time_delay, d, 'boolean', help=h)
        ol.add(o)
        
        d = 'Use echo technique'
        h = 'If set to True, w3af will checks insecure eval() usage by grepping'
        h += ' result of script execution for test strings.'
        o = option('useEcho', self._use_echo, d, 'boolean', help=h)
        ol.add(o)
        
        return ol

    def setOptions(self, optionsMap):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().

        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._use_time_delay = optionsMap['useTimeDelay'].getValue()
        self._use_echo = optionsMap['useEcho'].getValue()

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []

    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds eval() input injection vulnerabilities. These vulnerabilities are found in
        web applications, when the developer passes user controled data to the eval() function.
        To check for vulnerabilities of this kind, the plugin sends an echo function with two
        randomized strings as a parameters (echo 'abc' + 'xyz') and if the resulting HTML matches
        the string that corresponds to the evaluation of the expression ('abcxyz') then a
        vulnerability has been found.
        '''
