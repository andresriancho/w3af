'''
LDAPi.py

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
from __future__ import with_statement

from core.data.fuzzer.fuzzer import createMutants
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


class LDAPi(baseAuditPlugin):
    '''
    Find LDAP injection bugs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._errors = []
        
    def audit(self, freq ):
        '''
        Tests an URL for LDAP injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'LDAPi plugin is testing: ' + freq.getURL() )
        
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        ldapiStrings = self._get_LDAPi_strings()
        mutants = createMutants( freq , ldapiStrings, oResponse=oResponse )
            
        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug( 'LDAPi' , 'LDAPi', mutant.getURL() , mutant.getVar() ):
                
                targs = (mutant, )
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
                
        self._tm.join( self )
            
            
    def _get_LDAPi_strings( self ):
        '''
        Gets a list of strings to test against the web app.
        
        @return: A list with all LDAPi strings to test.
        '''
        ldap_strings = []
        ldap_strings.append("^(#$!@#$)(()))******")
        return ldap_strings

    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
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
            if self._hasNoBug( 'LDAPi' , 'LDAPi' , mutant.getURL() , mutant.getVar() ):
                
                ldap_error_list = self._find_ldap_error( response )
                for ldap_error_regex, ldap_error_string in ldap_error_list:
                    if not ldap_error_regex.search( mutant.getOriginalResponseBody(), re.IGNORECASE ):
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setId( response.id )
                        v.setSeverity(severity.HIGH)
                        v.setName( 'LDAP injection vulnerability' )
                        v.setDesc( 'LDAP injection was found at: ' + mutant.foundAt() )
                        v.addToHighlight( ldap_error_string )
                        kb.kb.append( self, 'LDAPi', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'LDAPi', 'LDAPi' ), 'VAR' )
        
    def _find_ldap_error( self, response ):
        '''
        This method searches for LDAP errors in html's.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for ldap_error_regex in self._get_ldap_errors():
            match = ldap_error_regex.search( response.getBody() , re.IGNORECASE )
            if  match:
                msg = 'Found LDAP error string. '
                msg += 'The error returned by the web application is (only a fragment is shown): "'
                msg += match.group(0) + '". The error was found on '
                msg += 'response with id ' + str(response.id) + '.'
                om.out.information(msg)
                res.append( (ldap_error_regex, match.group(0) ) )
        return res
        
    def _get_ldap_errors( self ):
        
        if len(self._errors) != 0:
            #
            #   This will use a little bit more of memory, but will increase the performance of the
            #   plugin considerably, because the regular expressions are going to be compiled
            #   only once, and then used many times.
            #
            return self._errors
            
        else:
            #
            #   Populate the self._errors list with the compiled versions of the regular expressions.
            #
            error_strings = []
        
            # Not sure which lang or LDAP engine
            error_strings.append('supplied argument is not a valid ldap')
            
            # Java
            error_strings.append('javax.naming.NameNotFoundException')
            error_strings.append('LDAPException')
            error_strings.append('com.sun.jndi.ldap')
            
            # PHP
            error_strings.append('Search: Bad search filter')
            
            # http://support.microsoft.com/kb/218185
            error_strings.append('Protocol error occurred')
            error_strings.append('Size limit has exceeded')
            error_strings.append('An inappropriate matching occurred')
            error_strings.append('A constraint violation occurred')
            error_strings.append('The syntax is invalid')
            error_strings.append('Object does not exist')
            error_strings.append('The alias is invalid')
            error_strings.append('The distinguished name has an invalid syntax')
            error_strings.append('The server does not handle directory requests')
            error_strings.append('There was a naming violation')
            error_strings.append('There was an object class violation')
            error_strings.append('Results returned are too large')
            error_strings.append('Unknown error occurred')
            error_strings.append('Local error occurred')
            error_strings.append('The search filter is incorrect')
            error_strings.append('The search filter is invalid')
            error_strings.append('The search filter cannot be recognized')
            
            # OpenLDAP
            error_strings.append('Invalid DN syntax')
            error_strings.append('No Such Object')
            
            # IPWorks LDAP
            # http://www.tisc-insight.com/newsletters/58.html
            error_strings.append('IPWorksASP.LDAP')
            
            # ???
            # https://entrack.enfoldsystems.com/browse/SERVERPUB-350
            error_strings.append('Module Products.LDAPMultiPlugins')
            
            #
            #   Now that I have the regular expressions in the "error_strings" list, I will compile
            #   them and save that into self._errors.
            #
            for re_string in error_strings:
                self._errors.append( re.compile(re_string) )
        
            return self._errors
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['grep.error500']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will find LDAP injections by sending a specially crafted string to every
        parameter and analyzing the response for LDAP errors.
        '''
