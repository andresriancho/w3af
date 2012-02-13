'''
mutant.py

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
import copy

from core.controllers.w3afException import w3afException
from core.data.dc.dataContainer import DataContainer

class mutant(object):
    '''
    This class is a wrapper for fuzzable requests that have been modified.
    '''
    def __init__(self, freq, israw=False):
        self._freq = freq
        self._fuzzableType = None
        self._var = ''
        self._index = 0
        self._originalValue = ''
        self._originalResponseBody = None
        self._mutant_dc = {}

    def getMutantDc(self):
        return self._mutant_dc

    def setMutantDc(self, dc):
        if not isinstance(dc, DataContainer):
            raise TypeError('Argument must be a DataContainer instance.')
        self._mutant_dc = dc
    #
    # this methods are from the mutant
    #
    def getFuzzableReq(self):
        return self._freq
    
    def setFuzzableReq(self, freq):
        self._freq = freq

    def setVar(self, var, index=0): 
        '''
        Set the name of the variable that this mutant modifies.
        
        @parameter var: The variable name that's being modified.
        @parameter index: The index. This was added to support repeated parameter names.
            a=123&a=456
        If I want to overwrite 456, index has to be 1.

        >>> from core.data.parsers.urlParser import url_object
        >>> from core.data.request.fuzzableRequest import fuzzableRequest
        >>> fr = fuzzableRequest(url_object('http://www.w3af.com'), )
        >>> m = mutant( fr )
        
        # By default
        >>> m.setVar( 'a' )
        >>> m.getVar()
        'a'
        >>> m.getVarIndex()
        0

        # With specific index
        >>> m.setVar( 'b', 3 )
        >>> m.getVar()
        'b'
        >>> m.getVarIndex()
        3
        
        '''
        self._var = var
        self._index = index
        
    def getVar( self ):
        return self._var
    
    def getVarIndex( self ):
        return self._index

    def setOriginalValue( self , v ):
        self._originalValue = v
        
    def getOriginalValue( self ):
        return self._originalValue
    
    def setModValue( self, val ):
        '''
        Set the value of the variable that this mutant modifies.
        '''
        try:
            self._freq._dc[ self.getVar() ][ self._index ] = val
        except Exception:
            msg = 'The mutant object wasn\'t correctly initialized. Either the variable to be'
            msg += ' modified, or the index of that variable are incorrect. This error was'
            msg += ' found in mutant.setModValue()'
            raise w3afException( msg )
        
    def getModValue( self ): 
        try:
            return self._freq._dc[ self.getVar() ][ self._index ]
        except:
            msg = 'The mutant object wasn\'t correctly initialized. Either the variable to be'
            msg += ' modified, or the index of that variable are incorrect. This error was'
            msg += ' found in mutant.getModValue()'
            raise w3afException( msg )
    
    def getMutantType( self ):
        msg = 'You should implement the getMutantType method when inheriting from mutant.'
        raise w3afException( msg )
    
    def printModValue( self ):
        return 'The sent '+ self.getMutantType() +' is: "' + str(self.getData()) + '" .'
    
    def __repr__( self ):
        return '<'+ self.getMutantType() +' mutant | '+ self.getMethod() +' | '+ self.getURI() +' >'
    
    def copy( self ):
        return copy.deepcopy( self )
    
    def getOriginalResponseBody( self ):
        '''
        The fuzzable request is a representation of a request; the original response body is the
        body of the response that is generated when w3af requests the fuzzable request for
        the first time.
        '''
        if self._originalResponseBody is None:
            raise ValueError, ('[mutant error] You should set the original '
                               'response body before getting its value!')
        return self._originalResponseBody
    
    def setOriginalResponseBody( self, orBody ):
        self._originalResponseBody = orBody
        
    #
    # All the other methods are forwarded to the fuzzable request except for
    # the magic methods.
    #
    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError, ("%s instance has no attribute '%s'" %
                                   (self.__class__.__name__, name))
        return getattr(self._freq, name)
        
    def foundAt(self):
        '''
        Return a string representing WHAT was fuzzed. This string
        is used like this:
            - v.setDesc('SQL injection in a '+ v['db'] +
                        ' was found at: ' + mutant.foundAt())
        '''
        res = ['"%s", using HTTP method %s. The sent data was: "'
               % (self.getURL(), self.getMethod())]
        
        # Depending on the data container, print different things:
        dc = self.getDc()
        dc_length = sum(
                map(lambda item: len(item[0])+len(item[1]), dc.items())
                )
        if dc_length > 65:
            res.append('...%s=%s..."' % (self.getVar(), self.getModValue()))
        else:
            res.append('%s".' % (dc,))
            if len(dc) > 1:
                res.append(' The modified parameter was "%s".' % self.getVar())

        return ''.join(res)
