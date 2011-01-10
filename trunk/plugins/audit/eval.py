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
from __future__ import with_statement

from core.data.fuzzer.fuzzer import createMutants
from core.data.fuzzer.fuzzer import createRandAlpha
import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity
from core.controllers.w3afException import w3afException

import re


class eval(baseAuditPlugin):
    '''
    Find insecure eval() usage.

    @author: Viktor Gazdag ( woodspeed@gmail.com ) & Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

        #Create some random strings, which the plugin will use.
        # for the fuzz_with_echo
        self._rnd1 = createRandAlpha(5)
        self._rnd2 = createRandAlpha(5)
        self._rndn = self._rnd1 + self._rnd2
        
        # And now for the fuzz_with_time_delay
        # The wait time of the unfuzzed request
        self._original_wait_time = 0
        # The wait time of the first test I'm going to perform
        self._wait_time = 4
        # The wait time of the second test I'm going to perform (this one is just to be sure!)
        self._second_wait_time = 9
        
        # User configured parameters
        self._use_time_delay = True
        self._use_echo = True

    def audit(self, freq ):
        '''
        Tests an URL for eval() user input injection vulnerabilities.
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'eval plugin is testing: ' + freq.getURL() )

        if self._use_echo:
            self._fuzz_with_echo( freq )
        
        #   Wait until the echo tests finish. I need to do this because of an odd problem with
        #   Python's "with" statement. It seems that if I use two different with statements and
        #   the same thread lock at the same time, the application locks and stops working.
        self._tm.join(self)
        
        if self._use_time_delay:
            self._fuzz_with_time_delay( freq )
            
        self._tm.join( self )

    def _fuzz_with_echo( self, freq ):
        '''
        Tests an URL for eval() usage vulnerabilities using echo strings.
        @param freq: A fuzzableRequest
        '''
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        print_strings = self._get_print_strings()
        mutants = createMutants( freq , print_strings, oResponse=oResponse )

        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'eval' , 'eval', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant,)
                kwds = {'analyze_callback':self._analyze_echo}
                self._tm.startFunction( target=self._sendMutant, args=targs, kwds=kwds, ownerObj=self )

    def _fuzz_with_time_delay( self, freq):
        '''
        Tests an URL for eval() usage vulnerabilities using time delays.
        @param freq: A fuzzableRequest
        '''
        res = self._sendMutant( freq, analyze=False, grepResult=False )
        self._original_wait_time = res.getWaitTime()

        # Prepare the strings to create the mutants
        wait_strings = self._get_wait_strings()
        mutants = createMutants( freq, wait_strings )

        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'eval' , 'eval', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant,)
                kwds = {'analyze_callback':self._analyze_wait}
                self._tm.startFunction( target=self._sendMutant, args=targs, kwds=kwds, ownerObj=self )
            

    def _analyze_echo( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method that was sent in the
        _fuzz_with_echo method.
        '''
        #
        #   Only one thread at the time can enter here. This is because I want to report each
        #   vulnerability only once, and by only adding the "if self._hasNoBug" statement, that
        #   could not be done.
        #
        with self._plugin_lock:
            
            #
            #   I will only report the vulnerability once.
            #
            if self._hasNoBug( 'eval' , 'eval' , mutant.getURL() , mutant.getVar() ):
                
                eval_error_list = self._find_eval_result( response )
                for eval_error in eval_error_list:
                    if not re.search( eval_error, mutant.getOriginalResponseBody(), re.IGNORECASE ):
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setId( response.id )
                        v.setSeverity(severity.HIGH)
                        v.setName( 'eval() input injection vulnerability' )
                        v.setDesc( 'eval() input injection was found at: ' + mutant.foundAt() )
                        kb.kb.append( self, 'eval', v )

    def _analyze_wait( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method that was sent in the
        _fuzz_with_time_delay method.
        '''
        #
        #   Only one thread at the time can enter here. This is because I want to report each
        #   vulnerability only once, and by only adding the "if self._hasNoBug" statement, that
        #   could not be done.
        #
        with self._plugin_lock:
            
            #
            #   I will only report the vulnerability once.
            #
            if self._hasNoBug( 'eval' , 'eval' , mutant.getURL() , mutant.getVar() ):
                        
                if response.getWaitTime() > (self._original_wait_time + self._wait_time - 2) and \
                response.getWaitTime() < (self._original_wait_time + self._wait_time + 2):
                    # generates a delay in the response; so I'll resend changing the time and see 
                    # what happens
                    originalWaitParam = mutant.getModValue()
                    moreWaitParam = originalWaitParam.replace( \
                                                                str(self._wait_time), \
                                                                str(self._second_wait_time) )
                    mutant.setModValue( moreWaitParam )
                    response = self._sendMutant( mutant, analyze=False )

                    if response.getWaitTime() > (self._original_wait_time + self._second_wait_time - 3) and \
                    response.getWaitTime() < (self._original_wait_time + self._second_wait_time + 3):
                        # Now I can be sure that I found a vuln, I control the time of the response.
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setId( response.id )
                        v.setSeverity(severity.HIGH)
                        v.setName( 'eval() input injection vulnerability' )
                        v.setDesc( 'eval() input injection was found at: ' + mutant.foundAt() )
                        kb.kb.append( self, 'eval', v )
                    else:
                        # The first delay existed... I must report something...
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setId( response.id )
                        i.setDc( mutant.getDc() )
                        i.setName( 'eval() input injection vulnerability' )
                        msg = 'eval() input injection was found at: ' + mutant.foundAt()
                        msg += ' . Please review manually.'
                        i.setDesc( msg )
                        kb.kb.append( self, 'eval', i )

    def _get_print_strings( self ):
        '''
        Gets a list of strings to test against the web app.
        @return: A list with all the strings to test.
        '''
        print_strings = []
        # PHP http://php.net/eval
        print_strings.append("echo \x27"+ self._rnd1 +"\x27 . \x27"+ self._rnd2 +"\x27;")
        # Perl http://perldoc.perl.org/functions/eval.html
        print_strings.append("print \x27"+ self._rnd1 +"\x27.\x27"+ self._rnd2 +"\x27;")
        # Python http://docs.python.org/reference/simple_stmts.html#the-exec-statement
        print_strings.append("print \x27"+ self._rnd1 +"\x27 + \x27"+ self._rnd2 +"\x27")
        # ASP
        print_strings.append("Response.Write\x28\x22"+self._rnd1+"+"+self._rnd2+"\x22\x29")
        return print_strings

    def _get_wait_strings( self ):
        '''
        Gets a list of strings to test against the web app.
        @return: A list with all the strings to test.
        '''
        wait_strings = []
        # PHP http://php.net/sleep
        # Perl http://perldoc.perl.org/functions/sleep.html
        wait_strings.append( "sleep(" + str( self._wait_time ) + ");" )
        
        # Python http://docs.python.org/library/time.html#time.sleep
        wait_strings.append( "import time;time.sleep(" + str( self._wait_time ) + ");" )
        
        # It seems that ASP doesn't support sleep! A language without sleep... is not a language!
        # http://classicasp.aspfaq.com/general/how-do-i-make-my-asp-page-pause-or-sleep.html
        
        # JSP takes the amount in miliseconds
        # http://java.sun.com/j2se/1.4.2/docs/api/java/lang/Thread.html#sleep(long)
        wait_strings.append( "Thread.sleep(" + str( self._wait_time * 1000) + ");" )
        
        # ASP.NET also uses miliseconds
        # http://msdn.microsoft.com/en-us/library/d00bd51t.aspx
        # Note: The Sleep in ASP.NET is uppercase
        wait_strings.append( "Thread.Sleep(" + str( self._wait_time * 1000) + ");" )
        
        return wait_strings

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'eval', 'eval' ), 'VAR' )

    def _find_eval_result( self, response ):
        '''
        This method searches for the randomized self._rndn string in html's.

        @parameter response: The HTTP response object
        @return: A list of error found on the page
        '''
        res = []
        for eval_error in self._get_eval_errors():
            match = re.search( eval_error, response.getBody() , re.IGNORECASE )
            if match:
                msg = 'Verified eval() input injection, found the concatenated random string: "'
                msg += response.getBody()[match.start():match.end()] + '" '
                msg += 'in the response body. '
                msg += 'The vulnerability was found on response with id ' + str(response.id) + '.'
                om.out.debug( msg )
                res.append( eval_error )
        return res

    def _get_eval_errors( self ):
        '''
        @return: The string that results from the evaluation of what I sent.
        '''
        print_str = []
        print_str.append( self._rndn )
        return print_str

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Use time delay (sleep() implementations)'
        h1 = 'If set to True, w3af will checks insecure eval() usage by analyzing'
        h1 += ' of time delay result of script execution.'
        o1 = option('useTimeDelay', self._use_time_delay, d1, 'boolean', help=h1)

        d2 = 'Use echo implementations'
        h2 = 'If set to True, w3af will checks insecure eval() usage by grepping'
        h2 += ' result of script execution for test strings.'
        o2 = option('useEcho', self._use_echo, d2, 'boolean', help=h2)

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def setOptions( self, optionsMap):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().

        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._use_time_delay = optionsMap['useTimeDelay'].getValue()
        self._use_echo = optionsMap['useEcho'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc( self ):
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
