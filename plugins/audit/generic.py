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

from core.data.fuzzer.fuzzer import createMutants, createRandNum, createRandAlNum
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.kb.vuln as vuln
import core.data.kb.info as info
from core.controllers.misc.levenshtein import relative_distance
import core.data.constants.severity as severity

class generic(baseAuditPlugin):
    '''
    Find all kind of bugs without using a fixed database of errors.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # User configured variables
        self._diffRatio = 0.35

    def _fuzzRequests(self, freq ):
        '''
        Find all kind of bugs without using a fixed database of errors.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'generic plugin is testing: ' + freq.getURL() )
        
        # First, get the original response.
        oResponse = self._sendMutant( freq , analyze=False )
        
        mutants = createMutants( freq , ['',], oResponse=oResponse )
        for m in mutants:
            # Now, we request the limit (something that doesn't exist)
            # If http://localhost/a.php?b=1 ; then I should request b=12938795  (random number)
            # If http://localhost/a.php?b=abc ; then I should request b=nasd9a8syfalsifyhalsf9y (random alnum)
            limitResponse = self._getLimitResponse( m )
            
            # Now I request something that could generate an error
            # If http://localhost/a.php?b=1 ; then I should request b=d'kcz'gj'"**5*(((*)
            # If http://localhost/a.php?b=abc ; then I should request b=d'kcz'gj'"**5*(((*)
            # I also try to trigger errors by sending empty strings
            # If http://localhost/a.php?b=1 ; then I should request b=
            # If http://localhost/a.php?b=abc ; then I should request b=
            for errorString in self._getErrorStrings():
                m.setModValue( errorString )
                errorResponse = self._sendMutant(  m , analyze=False )
            
                # Now I compare all responses
                self._analyzeResponses( oResponse, limitResponse, errorResponse, m )
          
    def _getErrorStrings( self ):
        '''
        @return: A list of strings that could generate errors. Please note that an empty string is something that,
        in most cases, is not tested. Although, I have found that it could trigger some errors.
        '''
        return ['d\'kc"z\'gj\'\"**5*(((;-*`)','']
       
    def _analyzeResponses( self, oResponse, limitResponse, errorResponse, mutant ):
        '''
        Analyze responses; if errorResponse doesn't look like oResponse nor limitResponse, then we have a vuln.
        @return: None
        '''
        originalToError = relative_distance(oResponse.getBody(), errorResponse.getBody() )
        limitToError = relative_distance( limitResponse.getBody(), errorResponse.getBody() )
        originalToLimit = relative_distance( limitResponse.getBody(), oResponse.getBody() )
        
        ratio = self._diffRatio + ( 1 - originalToLimit )
        
        #om.out.debug('originalToError: ' +  str(originalToError) )
        #om.out.debug('limitToError: ' +  str(limitToError) )
        #om.out.debug('originalToLimit: ' +  str(originalToLimit) )
        #om.out.debug('ratio: ' +  str(ratio) )
        
        if originalToError < ratio and limitToError < ratio:
            # Maybe the limit I requested wasn't really a non-existant one (and the error page really found the limit), 
            # let's request a new limit (one that hopefully doesn't exist)
            # This removes some false positives
            limitResponse2 = self._getLimitResponse( mutant )
            
            if relative_distance( limitResponse2.getBody(), limitResponse.getBody() ) > 1 - self._diffRatio:
                # The two limits are "equal"; It's safe to suppose that we have found the limit here
                # and that the error string really produced an error
                v = vuln.vuln( mutant )
                v.setId( errorResponse.id )
                v.setSeverity(severity.MEDIUM)
                v.setName( 'Unidentified vulnerability' )
                v.setDesc( 'An unidentified vulnerability was found at: ' + mutant.foundAt() )
                kb.kb.append( self, 'generic', v )
            else:
                # *maybe* and just *maybe* this is a vulnerability
                i = info.info( mutant )
                i.setId( errorResponse.id )
                i.setName( 'Possible unidentified vulnerability' )
                i.setDesc( '[Manual verification required] A possible vulnerability was found at: ' + mutant.foundAt() )
                kb.kb.append( self, 'generic', i )
    
    def _getLimitResponse( self, m ):
        # Copy the dc, needed to make a good vuln report
        dc = m.getDc().copy()
        
        if m.getOriginalValue().isdigit():
            m.setModValue( createRandNum(length=8) )
        else:
            m.setModValue( createRandAlNum(length=8) )
        limitResponse = self._sendMutant(  m , analyze=False )
        
        # restore the dc
        m.setDc( dc )
        return limitResponse
    
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
        d1 = 'If two strings have a diff ratio less than diffRatio, then they are *really* different'
        o1 = option('diffRatio', self._diffRatio, d1, 'float')
        
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
        self._diffRatio = optionsMap['diffRatio'].getValue()

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
