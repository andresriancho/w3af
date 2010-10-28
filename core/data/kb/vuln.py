'''
vuln.py

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

from core.controllers.w3afException import w3afException
from core.data.kb.info import info as info
from core.data.fuzzer.mutant import mutant as mutant


class vuln(info):
    '''
    This class represents a web vulnerability.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self, dataObj=None ):
        info.__init__( self, dataObj )
        
        # Default values
        self._method = None
        self._id = None
        self._dc = None
        self._severity = None
        self._variable = None
        self._mutant = None
        
        if isinstance( dataObj, mutant ) or isinstance( dataObj, vuln):
            self.setMethod( dataObj.getMethod() )
            # mutants dont have an ID, and sometimes I want to
            # create an instance of a vuln based on a mutant
            #self.setId( response.getId() )
            self.setDc( dataObj.getDc() )
            self.setVar( dataObj.getVar() )
            self.setURI( dataObj.getURI() )
            self.setMutant( dataObj )

    def setMutant( self, mutant ):
        '''
        Sets the mutant that created this vuln.
        '''
        self._mutant = mutant
        
    def getMutant( self ):
        return self._mutant
        
    def setVar( self, variable ):
        self._variable = variable

    def setDc( self, dc ):
        self._dc = dc
        
    def setSeverity( self, severity ):
        self._severity = severity
        
    def getMethod( self ):
        if self._mutant:
            return self._mutant.getMethod()
        else:
            return self._method

    def getVar( self ):
        if self._mutant:
            return self._mutant.getVar()
        else:
            return self._variable

    def getDc( self ):
        if self._mutant:
            return self._mutant.getDc()
        else:
            return self._dc
    
    def getSeverity( self ):
        return self._severity
        
    def getDesc( self ):
        if self._id is not None and self._id != 0:
            if not self._desc.endswith('.'):
                self._desc += '.'
            
            # One request OR more than one request
            desc_to_return = self._desc
            if len(self._id) > 1:
                desc_to_return += ' This vulnerability was found in the requests with'
                desc_to_return += ' ids ' + self._convert_to_range_wrapper( self._id ) + '.'
            else:
                desc_to_return += ' This vulnerability was found in the request with'
                desc_to_return += ' id ' + str(self._id[0]) + '.'
                
            return desc_to_return
        else:
            return self._desc
            
    def __repr__( self ):
        return '<vuln object for vulnerability: "'+self._desc+'">'
