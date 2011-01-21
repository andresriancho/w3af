'''
blind_sqli_response_diff.py

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


from core.data.fuzzer.fuzzer import createMutants, createRandNum
import core.controllers.outputManager as om

import core.data.kb.vuln as vuln
import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity

from core.controllers.w3afException import w3afException

import re

# importing this to have sendMutant and setUrlOpener
from core.controllers.basePlugin.basePlugin import basePlugin

class blind_sqli_response_diff(basePlugin):
    '''
    This class tests for blind SQL injection bugs using response diffing,
    the logic is here and not as an audit plugin because this logic is also used in attack plugins.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        # ""I'm a plugin""
        basePlugin.__init__(self)
        
        # User configured variables
        self._equalLimit = 0.8
        self._equAlgorithm = 'setIntersection'
        
    def setEqualLimit( self, _equalLimit ):
        '''
        Most of the equal algorithms use a rate to tell if two responses 
        are equal or not. 1 is 100% equal, 0 is totally different.
        
        @parameter _equalLimit: The equal limit to use.
        '''
        self._equalLimit = _equalLimit
        
    def setEquAlgorithm( self, _equAlgorithm ):
        '''
        @parameter _equAlgorithm: The equal algorithm to use.
        '''
        self._equAlgorithm = _equAlgorithm
        
    def is_injectable( self, freq, parameter ):
        '''
        Check if "parameter" of the fuzzable request object is injectable or not.
        
        @freq: The fuzzableRequest object that I have to modify
        @parameter: A string with the parameter name to test
        
        @return: A vulnerability object or None if nothing is found
        '''
        dummy = ['', ]
        parameter_to_test = [ parameter, ]
        mutants = createMutants( freq , dummy, fuzzableParamList=parameter_to_test )
        
        for mutant in mutants:
            statements = self._get_statements( mutant )
            for statement_type in statements:
                vuln = self._findBsql( mutant, statements[statement_type], statement_type )
                if vuln:
                    return vuln
        
        return None
    
    def _get_statements( self, mutant, excludeNumbers=[] ):
        '''
        Returns a list of statement tuples.
        '''
        res = {}
        rndNum = int( createRandNum( 2 , excludeNumbers ) )
        rndNumPlusOne = rndNum +1
        
        if mutant.getOriginalValue() == '':
            # I use this when I don't have a value setted in the original request
            
            # Unquoted, integer values
            trueStm = '%i OR %i=%i ' % (rndNum, rndNum, rndNum )
            falseStm = '%i AND %i=%i ' % (rndNum, rndNum, rndNumPlusOne)
            res['numeric'] = ( trueStm, falseStm )
            # Single quotes
            trueStm = "%i' OR '%i'='%i" % (rndNum, rndNum, rndNum )
            falseStm = "%i' AND '%i'='%i" % (rndNum, rndNum, rndNumPlusOne)
            res['stringsingle'] = ( trueStm, falseStm)
            # Double quotes
            trueStm = '%i" OR "%i"="%i' % (rndNum, rndNum, rndNum )
            falseStm = '%i" AND "%i"="%i' % (rndNum, rndNum, rndNumPlusOne)
            res['stringdouble'] = ( trueStm, falseStm)
        else:
            # I use this when I HAVE a value setted in the original request
            # Unquoted, integer values, they should only be used if the original value is a number
            # if it's something like 1209jas and it's used in a WHERE... then it MUST be quoted.
            oval = mutant.getOriginalValue()
            if oval.isdigit():
                trueStm = oval + ' OR %i=%i ' % (rndNum, rndNum )
                falseStm = oval + ' AND %i=%i ' % (rndNum, rndNumPlusOne)
                res['numeric'] = ( trueStm, falseStm )
            
            # Single quotes
            trueStm = oval + "' OR '%i'='%i" % (rndNum, rndNum )
            falseStm = oval + "' AND '%i'='%i" % (rndNum, rndNumPlusOne)
            res['stringsingle'] = ( trueStm, falseStm)
            # Double quotes
            trueStm = oval + '" OR "%i"="%i' % ( rndNum, rndNum )
            falseStm = oval + '" AND "%i"="%i' % ( rndNum, rndNumPlusOne)
            res['stringdouble'] = ( trueStm, falseStm)
            
        return res
    
    def _findBsqlAux( self, mutant, statementTuple, statement_type, saveToKb ):
        '''
        Auxiliar function that does almost nothing.
        '''
        bsqlVulns = self._findBsql( mutant, statementTuple, statement_type )
        if saveToKb:
            for bsqlVuln in bsqlVulns:
                om.out.vulnerability( bsqlVuln.getDesc() )
                kb.kb.append( 'blindSqli', 'blindSqli', bsqlVuln )
                
    def _findBsql( self, mutant, statementTuple, statement_type ):
        '''
        Is the main algorithm for finding blind sql injections.
        
        @return: A vulnerability object or None if nothing is found
        '''
        trueStatement = statementTuple[0]
        falseStatement = statementTuple[1]
        
        mutant.setModValue( trueStatement )
        trueResponse = self._sendMutant( mutant, analyze=False )

        mutant.setModValue( falseStatement )
        falseResponse = self._sendMutant( mutant, analyze=False )
        
        om.out.debug('Comparing trueResponse and falseResponse.')
        if not self.equal( trueResponse.getBody() , falseResponse.getBody() ):
            
            sintaxError = "d'z'0"
            mutant.setModValue( sintaxError )
            seResponse = self._sendMutant( mutant, analyze=False )
            
            om.out.debug('Comparing trueResponse and sintaxErrorResponse.')
            if not self.equal( trueResponse.getBody() , seResponse.getBody() ):
                
                # Verify the injection!
                statements = self._get_statements( mutant )
                secondTrueStm = statements[ statement_type ][0]
                secondFalseStm = statements[ statement_type ][1]
                
                mutant.setModValue( secondTrueStm )
                secondTrueResponse = self._sendMutant( mutant, analyze=False )

                mutant.setModValue( secondFalseStm )
                secondFalseResponse = self._sendMutant( mutant, analyze=False ) 
                
                om.out.debug('Comparing secondTrueResponse and trueResponse.')
                if self.equal( secondTrueResponse.getBody(), trueResponse.getBody() ):
                    
                    om.out.debug('Comparing secondFalseResponse and falseResponse.')
                    if self.equal( secondFalseResponse.getBody(), falseResponse.getBody() ):
                        v = vuln.vuln( mutant )
                        v.setId( [secondFalseResponse.id, secondTrueResponse.id] )
                        v.setSeverity(severity.HIGH)
                        v.setName( 'Blind SQL injection vulnerability' )
                        # This is needed to be used in fuzz file name
                        v.getMutant().setOriginalValue( '' )
                        v.getMutant().setModValue( '' )
                        
                        desc = 'Blind SQL injection was found at: "' + v.getURL()  + '",'
                        desc += ' using HTTP method ' + v.getMethod() + '.'
                        desc += ' The injectable parameter is: "' + mutant.getVar() + '".'
                        v.setDesc( desc )
                        om.out.debug( v.getDesc() )
                        
                        v['type'] = statement_type
                        v['trueHtml'] = secondTrueResponse.getBody()
                        v['falseHtml'] = secondFalseResponse.getBody()
                        v['errorHtml'] = seResponse.getBody()
                        return v
                        
        return None
        
    def equal( self, body1, body2 ):
        '''
        Determines if two pages are equal using some tricks.
        '''
        if self._equAlgorithm == 'setIntersection':
            return self._setIntersection( body1, body2)
        elif self._equAlgorithm == 'stringEq':
            return self._stringEq( body1, body2)
            
        raise w3afException('Unknown algorithm selected.')
    
    def _stringEq( self, body1 , body2 ):
        '''
        This is one of the equal algorithms.
        '''
        if body1 == body2:
            om.out.debug('Pages are equal.')
            return True
        else:
            om.out.debug('Pages are NOT equal.')
            return False
        
    def _setIntersection( self, body1, body2 ):
        '''
        This is one of the equal algorithms.
        '''
        sb1 = re.findall('(\w+)', body1)
        sb2 = re.findall('(\w+)', body2)
        
        setb1 = set( sb1 )
        setb2 = set( sb2 )
        
        intersection = setb1.intersection( setb2 )
        
        totalLen = float( len( setb1 ) + len( setb2 ) )
        if totalLen == 0:
            om.out.debug( 'The length of both pages is zero. Cant apply setIntersection.' )
            return False
        equal = ( 2 * len(intersection) ) / totalLen 
        
        if equal > self._equalLimit:
            om.out.debug('Pages are equal, match rate: ' + str(equal) )
            return True
        else:
            om.out.debug('Pages are NOT equal, match rate: ' + str(equal) )
            return False
    

