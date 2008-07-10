'''
info.py

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
from core.data.parsers.urlParser import *
import core.data.constants.severity as severity

class info(dict):
    '''
    This class represents an information that is saved to the kb.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, dataObj=None):
        
        # Default values
        self._url = ''
        self._uri = ''
        self._desc = ''
        self._method = ''
        self._variable = ''
        self._id = None
        self._name = ''
        self._dc = None
            
        # Clone the object!
        if isinstance( dataObj, info ):
            self.setURI( dataObj.getURI() )
            self.setDesc( dataObj.getDesc() )
            self.setMethod( dataObj.getMethod() )
            self.setVar( dataObj.getVar() )
            self.setId( dataObj.getId() )
            self.setName( dataObj.getName() )
            self.setDc( dataObj.getDc() )
            for k in dataObj.keys():
                self[ k ] = dataObj[ k ]
    
    def getSeverity( self ):
        '''
        @return: severity.INFORMATION , all information objects have the same level of severity.
        '''
        return severity.INFORMATION
    
    def setName( self, name ):
        self._name = name
        
    def getName( self ):
        return self._name
    
    def setURL( self, url ):
        self._url = uri2url( url )
    
    def setURI( self, uri ):
        self._uri = uri
        self._url = uri2url( uri )
    
    def setMethod( self, method ):
        self._method = method.upper()
    
    def getMethod( self ):
        return self._method
        
    def setDesc( self, desc ):
        self._desc = desc
        
    def getURL( self ):
        return self._url
    
    def getURI( self ):
        return self._uri
        
    def getDesc( self ):
        if self._id != None and self._id != 0:
            if not self._desc.strip().endswith('.'):
                self._desc += '.'
            return self._desc + ' This information was found in the request with id ' + str(self._id) + '.'
        else:
            return self._desc
            
    def __str__( self ):
        return self._desc
        
    def __repr__( self ):
        return '<info object for issue: "'+self._desc+'">'
        
    def setId( self, id ):
        '''
        This is is the one from the response object that uniquely identifies all 
        requests and responses.
        '''
        self._id = id
    
    def getId( self ):
        '''
        This is is the one from the response object that uniquely identifies all 
        requests and responses.
        '''
        return self._id
        
    def setVar( self, variable ):
        self._variable = variable
        
    def getVar( self ):
        return self._variable
        
    def setDc( self, dc ):
        self._dc = dc
        
    def getDc( self ):
        return self._dc
        
