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

from core.data.fuzzer.fuzzer import createMutants
from core.data.fuzzer.fuzzer import createRandAlpha
import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
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
        self._rnd1 = createRandAlpha(5)
        self._rnd2 = createRandAlpha(5)
        self._rndn = self._rnd1 + self._rnd2
        # The wait time of the unfuzzed request
        self._originalWaitTime = 0
        # The wait time of the first test I'm going to perform
        self._waitTime = 4
        # The wait time of the second test I'm going to perform (this one is just to be sure!)
        self._secondWaitTime = 9
        # User configured parameters
        self._useTimeDelay = True
        self._useEcho = True

    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for eval() user input injection vulnerabilities.
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'eval plugin is testing: ' + freq.getURL() )

        if self._useEcho:
            self._fuzzWithEcho( freq )

        if self._useTimeDelay:
            self._fuzzWithTimeDelay( freq )

    def _fuzzWithEcho( self, freq ):
        '''
        Tests an URL for eval() usage vulnerabilities using echo strings.
        @param freq: A fuzzableRequest
        '''
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        evalStrings = self._getEvalStrings()
        mutants = createMutants( freq , evalStrings, oResponse=oResponse )

        for mutant in mutants:
            if self._hasNoBug( 'eval' , 'eval' , mutant.getURL() , mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                kwds = {'analyze_callback':self._analyzeEcho}
                self._tm.startFunction( target=self._sendMutant, args=targs,\
                        kwds=kwds, ownerObj=self )

    def _fuzzWithTimeDelay( self, freq):
        '''
        Tests an URL for eval() usage vulnerabilities using time delays.
        @param freq: A fuzzableRequest
        '''
        res = self._sendMutant( freq, analyze=False, grepResult=False )
        self._originalWaitTime = res.getWaitTime()

        # Prepare the strings to create the mutants
        waitStrings = self._getWaitStrings()
        mutants = createMutants( freq, waitStrings )

        for mutant in mutants:
            if self._hasNoBug( 'eval', 'eval', mutant.getURL() , mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                kwds = {'analyze_callback':self._analyzeWait}
                self._tm.startFunction( target=self._sendMutant, args=targs , \
                                                    kwds=kwds, ownerObj=self )

    def _analyzeEcho( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method that was sent in the
        _fuzzWithEcho method.
        '''
        evalErrorList = self._findEvalError( response )
        for evalError in evalErrorList:
            if not re.search( evalError, mutant.getOriginalResponseBody(), re.IGNORECASE ):
                v = vuln.vuln( mutant )
                v.setId( response.id )
                v.setSeverity(severity.HIGH)
                v.setName( 'eval() input injection vulnerability' )
                v.setDesc( 'eval() input injection was found at: ' + mutant.foundAt() )
                kb.kb.append( self, 'eval', v )

    def _analyzeWait( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method that was sent in the
        _fuzzWithTimeDelay method.
        '''
        if response.getWaitTime() > (self._originalWaitTime + self._waitTime - 2) and \
        response.getWaitTime() < (self._originalWaitTime + self._waitTime + 2):
            # generates a delay in the response; so I'll resend changing the time and see 
            # what happens
            originalWaitParam = mutant.getModValue()
            moreWaitParam = originalWaitParam.replace( \
                                                        str(self._waitTime), \
                                                        str(self._secondWaitTime) )
            mutant.setModValue( moreWaitParam )
            response = self._sendMutant( mutant, analyze=False )

            if response.getWaitTime() > (self._originalWaitTime + self._secondWaitTime - 3) and \
            response.getWaitTime() < (self._originalWaitTime + self._secondWaitTime + 3):
                # Now I can be sure that I found a vuln, I control the time of the response.
                v = vuln.vuln( mutant )
                v.setId( response.id )
                v.setSeverity(severity.HIGH)
                v.setName( 'eval() input injection vulnerability' )
                v.setDesc( 'eval() input injection was found at: ' + mutant.foundAt() )
                kb.kb.append( self, 'eval', v )
            else:
                # The first delay existed... I must report something...
                i = info.info()
                i.setId( response.id )
                i.setSeverity(severity.HIGH)
                i.setName( 'eval() input injection vulnerability' )
                msg = 'eval() input injection was found at: ' + mutant.foundAt()
                msg += ' . Please review manually.'
                i.setDesc( msg )
                kb.kb.append( self, 'eval', i )

    def _getEvalStrings( self ):
        '''
        Gets a list of strings to test against the web app.
        @return: A list with all the strings to test.
        '''
        evalStrings = []
        # PHP http://php.net/eval
        evalStrings.append("echo \x27"+ self._rnd1 +"\x27 . \x27"+ self._rnd2 +"\x27;")
        # Perl http://perldoc.perl.org/functions/eval.html
        evalStrings.append("print \x27"+ self._rnd1 +"\x27.\x27"+ self._rnd2 +"\x27;")
        # Python http://docs.python.org/reference/simple_stmts.html#the-exec-statement
        evalStrings.append("print \x27"+ self._rnd1 +"\x27 + \x27"+ self._rnd2 +"\x27")
        # ASP
        evalStrings.append("Response.Write\x28\x22"+self._rnd1+"+"+self._rnd2+"\x22\x29")
        return evalStrings

    def _getWaitStrings( self ):
        '''
        Gets a list of strings to test against the web app.
        @return: A list with all the strings to test.
        '''
        waitStrings = []
        # PHP http://php.net/sleep
        waitStrings.append( "sleep(" + str( self._waitTime ) + ");" )
        # Perl http://perldoc.perl.org/functions/sleep.html
        waitStrings.append( "sleep(" + str( self._waitTime ) + ");" )
        # Python http://docs.python.org/library/time.html#time.sleep
        waitStrings.append( "import time;time.sleep(" + str( self._waitTime ) + ");" )
        return waitStrings

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'eval', 'eval' ), 'VAR' )

    def _findEvalError( self, response ):
        '''
        This method searches for the randomized self._rndn string in html's.

        @parameter response: The HTTP response object
        @return: A list of error found on the page
        '''
        res = []
        for evalError in self._getEvalErrors():
            match = re.search( evalError, response.getBody() , re.IGNORECASE )
            if match:
                msg = 'Verified eval() input injection, found the concatenated random string: "'
                msg += response.getBody()[match.start():match.end()] + '" '
                msg += 'in the response body. '
                msg += 'The vulnerability was found on response with id ' + str(response.id) + '.'
                om.out.debug( msg )
                res.append( evalError )
        return res

    def _getEvalErrors( self ):
        '''
        @return: The string that results from the evaluation of what I sent.
        '''
        errorStr = []
        errorStr.append( self._rndn )
        return errorStr

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Use time delay (sleep() implementations)'
        h1 = 'If set to True, w3af will checks insecure eval() usage by analyzing'
        h1 += ' of time delay result of script execution.'
        o1 = option('useTimeDelay', self._useTimeDelay, d1, 'boolean', help=h1)

        d2 = 'Use echo implementations'
        h2 = 'If set to True, w3af will checks insecure eval() usage by grepping'
        h2 += ' result of script execution for test strings.'
        o2 = option('useEcho', self._useEcho, d2, 'boolean', help=h2)

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
        self._useTimeDelay = optionsMap['useTimeDelay'].getValue()
        self._useEcho = optionsMap['useEcho'].getValue()

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
        This plugin finds eval() input injection vulnerabilities. These vulnerabilities are found in web applications, when the developer
        passes user controled data to the eval() function. To check for vulnerabilities of this kind, the plugin sends an echo function
        with two randomized strings as a parameters (echo 'abc' + 'xyz') and if the resulting HTML matches the string that corresponds
        to the evaluation of the expression ('abcxyz') then a vulnerability has been found.
        '''
