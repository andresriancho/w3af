'''
blindSqli.py

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


from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
import core.data.kb.vuln as vuln
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.controllers.threads.threadManager import threadManager as tm
from core.controllers.w3afException import w3afException
# importing this to have sendMutant and setUrlOpener
from core.controllers.basePlugin.basePlugin import basePlugin
import re
import core.data.constants.severity as severity

class blindSqli(basePlugin):
    '''
    This class tests for blind SQL injection bugs, the logic is here and not as an audit plugin cause 
    this logic is also used in attack plugins.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        # User configured variables
        self._equalLimit = 0.8
        self._equAlgorithm = 'setIntersection'
        self._tm = tm()
        
    def setEqualLimit( self, _equalLimit ):
        self._equalLimit = _equalLimit
        
    def setEquAlgorithm( self, _equAlgorithm ):
        self._equAlgorithm = _equAlgorithm
    
        
    def verifyBlindSQL( self, freq, parameter ):
        '''
        Verify the existance of an already found vuln.
        '''
        dummy = ['',]
        parameterToTest = [ parameter, ]
        mutants = createMutants( freq , dummy, fuzzableParamList=parameterToTest )
        
        for mutant in mutants:
            statements = self._getStatements( mutant )
            for statementType in statements:
                vulns = self._findBsql( mutant, statements[statementType], statementType )
                if len( vulns ):
                    return vulns
        
        return []
        
    def findBlindSQL(self, fuzzableRequest, saveToKb=False ):
        '''
        Tests an URL for blind Sql injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        dummy = ['',]
        mutants = createMutants( fuzzableRequest , dummy )
        
        for mutant in mutants:
            statements = self._getStatements( mutant )
            for statementType in statements:
                targs = (mutant,statements[ statementType ], statementType, saveToKb)
                self._tm.startFunction( target=self._findBsqlAux, args=targs, ownerObj=self )
        
        self._tm.join( self )
    
    def _getStatements( self, mutant, excludeNumbers=[] ):
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
    
    def _findBsqlAux( self, mutant, statementTuple, statementType, saveToKb ):
        '''
        Auxiliar function that does almost nothing.
        '''
        bsqlVulns = self._findBsql( mutant, statementTuple, statementType )
        if saveToKb:
            for vuln in bsqlVulns:
                om.out.vulnerability( vuln.getDesc() )
                kb.kb.append( self, 'blindSqli', vuln )
                
    def _findBsql( self, mutant, statementTuple, statementType ):
        '''
        Is the main algorithm for finding blind sql injections.
        '''
        res = []
        
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
                statements = self._getStatements( mutant )
                secondTrueStm = statements[ statementType ][0]
                secondFalseStm = statements[ statementType ][1]
                
                mutant.setModValue( secondTrueStm )
                secondTrueResponse = self._sendMutant( mutant, analyze=False )

                mutant.setModValue( secondFalseStm )
                secondFalseResponse = self._sendMutant( mutant, analyze=False ) 
                
                om.out.debug('Comparing secondTrueResponse and trueResponse.')
                if self.equal( secondTrueResponse.getBody(), trueResponse.getBody() ):
                    
                    om.out.debug('Comparing secondFalseResponse and falseResponse.')
                    if self.equal( secondFalseResponse.getBody(), falseResponse.getBody() ):
                        v = vuln.vuln( mutant )
                        v.setId( secondFalseResponse.id )
                        v.setSeverity(severity.HIGH)
                        v.setName( 'Blind SQL injection vulnerability' )
                        # This is needed to be used in fuzz file name
                        v.getMutant().setOriginalValue( '' )
                        v.getMutant().setModValue( '' )
                        
                        v.setDesc( 'Blind SQL injection was found at: ' + v.getURL() + ' . Using method: ' + v.getMethod() + '. The injectable parameter is: ' + mutant.getVar() )
                        om.out.debug( v.getDesc() )
                        v['type'] = statementType
                        v['trueHtml'] = secondTrueResponse.getBody()
                        v['falseHtml'] = secondFalseResponse.getBody()
                        v['errorHtml'] = seResponse.getBody()
                        res.append( v )
                        
        return res
        
    def equal( self, body1, body2 ):
        '''
        Determines if two pages are equal using some tricks.
        '''
        if self._equAlgorithm == 'setIntersection':
            return self._setIntersection( body1, body2)
        elif self._equAlgorithm == 'stringEq':
            return self._stringEq( body1, body2)
        elif self._equAlgorithm == 'intelligentCut':
            return self._intelligentCut( body1, body2)
            
        raise w3afException('Unknown algorithm selected.')
    
    def _intelligentCut( self, body1, body2 ):
        '''
        This is one of the equal algorithms. The idea is to remove the sections of the html that change from one call to another.
        '''
        raise w3afException('_intelligentCut is not implemented yet.')
        
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
        sb1 = re.findall('(\w+)',body1 )
        sb2 = re.findall('(\w+)',body2 )
        
        setb1 = set( sb1 )
        setb2 = set( sb2 )
        
        intersection = setb1.intersection( setb2 )
        
        totalLen = float( len( setb1 ) + len( setb2 ) )
        if totalLen == 0:
            om.out.error( 'The length of both pages are zero. Cant work with this.' )
            return False
        equal = ( 2 * len(intersection) ) / totalLen 
        
        if equal > self._equalLimit:
            om.out.debug('Pages are equal, match rate: ' + str(equal) )
            return True
        else:
            om.out.debug('Pages are NOT equal, match rate: ' + str(equal) )
            return False
    

