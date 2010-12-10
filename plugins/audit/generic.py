'''
generic.py

Copyright 2007 Andres Riancho

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
from core.data.fuzzer.fuzzer import createMutants, createRandNum, createRandAlNum
from core.controllers.misc.levenshtein import relative_distance

import copy


class generic(baseAuditPlugin):
    '''
    Find all kind of bugs without using a fixed database of errors.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        #   Internal variables
        self._already_reported = []
        
        #   User configured variables
        self._diff_ratio = 0.30

    def audit(self, freq ):
        '''
        Find all kind of bugs without using a fixed database of errors.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'generic plugin is testing: ' + freq.getURL() )
        
        # First, get the original response and create the mutants
        oResponse = self._sendMutant( freq , analyze=False )
        mutants = createMutants( freq , ['', ] , oResponse=oResponse )
        
        for m in mutants:
            
            #   First I check that the current modified parameter in the mutant doesn't have
            #   an already reported vulnerability. I don't want to report vulnerabilities more
            #   than once.
            if (m.getURL(), m.getVar()) in self._already_reported:
                continue
            
            # Now, we request the limit (something that doesn't exist)
            # If http://localhost/a.php?b=1 ; then I should request b=12938795  (random number)
            # If http://localhost/a.php?b=abc ; then I should request b=hnv98yks (random alnum)
            limit_response = self._get_limit_response( m )
            
            # Now I request something that could generate an error
            # If http://localhost/a.php?b=1 ; then I should request b=d'kcz'gj'"**5*(((*)
            # If http://localhost/a.php?b=abc ; then I should request b=d'kcz'gj'"**5*(((*)
            # I also try to trigger errors by sending empty strings
            # If http://localhost/a.php?b=1 ; then I should request b=
            # If http://localhost/a.php?b=abc ; then I should request b=
            for error_string in self._get_error_strings():
                m.setModValue( error_string )
                error_response = self._sendMutant(  m , analyze=False )
            
                # Now I compare all responses
                self._analyzeResponses( oResponse, limit_response, error_response, m )
          
    def _get_error_strings( self ):
        '''
        @return: A list of strings that could generate errors. Please note that an empty string is something that,
        in most cases, is not tested. Although, I have found that it could trigger some errors.
        '''
        return ['d\'kc"z\'gj\'\"**5*(((;-*`)', '']
       
    def _analyzeResponses( self, oResponse, limit_response, error_response, mutant ):
        '''
        Analyze responses; if error_response doesn't look like oResponse nor limit_response,
        then we have a vuln.
        
        @return: None
        '''
        original_to_error = relative_distance(oResponse.getBody(), error_response.getBody() )
        limit_to_error = relative_distance( limit_response.getBody(), error_response.getBody() )
        original_to_limit = relative_distance( limit_response.getBody(), oResponse.getBody() )
        
        ratio = self._diff_ratio + ( 1 - original_to_limit )
        
        #om.out.debug('original_to_error: ' +  str(original_to_error) )
        #om.out.debug('limit_to_error: ' +  str(limit_to_error) )
        #om.out.debug('original_to_limit: ' +  str(original_to_limit) )
        #om.out.debug('ratio: ' +  str(ratio) )
        
        if original_to_error < ratio and limit_to_error < ratio:
            # Maybe the limit I requested wasn't really a non-existant one
            # (and the error page really found the limit), 
            # let's request a new limit (one that hopefully doesn't exist)
            # in order to remove some false positives
            limit_response2 = self._get_limit_response( mutant )
            
            if relative_distance( limit_response2.getBody(), limit_response.getBody() ) > \
            1 - self._diff_ratio:
                # The two limits are "equal"; It's safe to suppose that we have found the
                # limit here and that the error string really produced an error
                v = vuln.vuln( mutant )
                v.setPluginName(self.getName())
                v.setId( error_response.id )
                v.setSeverity(severity.MEDIUM)
                v.setName( 'Unidentified vulnerability' )
                v.setDesc( 'An unidentified vulnerability was found at: ' + mutant.foundAt() )
                kb.kb.append( self, 'generic', v )
                self._already_reported.append( (mutant.getURL(), mutant.getVar()) )
            else:
                # *maybe* and just *maybe* this is a vulnerability
                i = info.info( mutant )
                i.setPluginName(self.getName())
                i.setId( error_response.id )
                i.setName( 'Possible unidentified vulnerability' )
                msg = '[Manual verification required] A possible vulnerability was found at: '
                msg += mutant.foundAt()
                i.setDesc( msg )
                kb.kb.append( self, 'generic', i )
                self._already_reported.append( (mutant.getURL(), mutant.getVar()) )
    
    def _get_limit_response( self, m ):
        '''
        We request the limit (something that doesn't exist)
            - If http://localhost/a.php?b=1 ; then I should request b=12938795  (random number)
            - If http://localhost/a.php?b=abc ; then I should request b=hnv98yks (random alnum)
        
        @return: The limit response object
        '''
        # Copy the dc, needed to make a good vuln report
        dc = copy.deepcopy(m.getDc())
        
        if m.getOriginalValue().isdigit():
            m.setModValue( createRandNum(length=8) )
        else:
            m.setModValue( createRandAlNum(length=8) )
        limit_response = self._sendMutant(  m , analyze=False )
        
        # restore the dc
        m.setDc( dc )
        return limit_response
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        vulnsAndInfos = kb.kb.getAllVulns()
        vulnsAndInfos.extend( kb.kb.getAllInfos() )
        self.printUniq( vulnsAndInfos, 'VAR' )

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'If two strings have a diff ratio less than diffRatio, then they are '
        d1 += '*really* different'
        o1 = option('diffRatio', self._diff_ratio, d1, 'float')
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._diff_ratio = optionsMap['diffRatio'].getValue()

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
        This plugin finds all kind of bugs without using a fixed database of errors. This is a new
        kind of methodology that solves the main problem of most web application security scanners.        
        '''
