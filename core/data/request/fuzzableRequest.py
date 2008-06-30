'''
fuzzableRequest.py

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
import core.controllers.outputManager as om
from core.data.dc.dataContainer import dataContainer as dc
from core.data.dc.cookie import cookie as cookie
import core.data.kb.config as cf
from core.data.parsers.urlParser import *
import copy

class fuzzableRequest:
    '''
    This class represents a fuzzable request. Fuzzable requests where created to allow w3af plugins
    to be much simpler and dont really care if the vulnerability is in the postdata, querystring, header, cookie
    or some other variable.
    
    Other classes should inherit from this one and change the behaviour of getURL() and getData(). For
    example: the class httpQsRequest should return the _dc in the querystring ( getURL ) and httpPostDataRequest
    should return the _dc in the POSTDATA ( getData() ).
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        # Internal variables
        self._url = ''
        self._method = 'GET'
        self._uri = ''
        self._data = ''
        self._headers = {}
        self._cookie = None
        self._dc = dc()
    
    def dump( self ):
        '''
        @return: a DETAILED str representation of this fuzzable request.
        '''
        strRes = ''
        strRes += self.dumpRequestHead()
        strRes += '\n\n'
        strRes += str( self.getData() )
        return strRes
    
    def dumpRequestHead( self ):
        '''
        @return: A string with the head of the request
        '''
        res = ''
        res += self.getMethod() + ' ' + self.getURI() + ' ' + 'HTTP/1.1\n'
        res += self.dumpHeaders()
        return res
    
    def dumpHeaders( self ):
        '''
        @return: a str representation of the headers.
        '''
        strRes = ''
        for header in self._headers:
            strRes += header + ': ' + self._headers[ header ] + '\n'
        return strRes
        
    def __str__( self ):
        '''
        Return a str representation of this fuzzable request.
        '''
        strRes = ''
        strRes += self._url
        strRes += ' | Method: ' + self._method
        if self._dc:
            strRes += ' | Parameters: ('
            for i in self._dc:
                strRes += i + ','
            strRes = strRes[: -1]
            strRes += ')'
        return strRes
        
    def __eq__( self, other ):
        if self._uri == other._uri and\
        self._method == other._method and\
        self._dc == other._dc:
            return True
        else:
            return False
    
    def __ne__( self,other):
        return not self.__eq__( other )
    
    def setURL( self , url ):
        self._url = url.replace(' ', '%20')
        self._uri = self._url
    
    def setURI( self, uri ):
        self._uri = uri.replace(' ', '%20')
        self._url = uri2url( uri )
        
    def setMethod( self , method ):
        self._method = method
        
    def setDc( self , dataCont ):
        if isinstance(dataCont, dc):
            self._dc = dataCont
        else:
            raise w3afException('Invalid call to fuzzableRequest.setDc(), the argument must be a dataContainer instance.')
        
    def setHeaders( self , headers ):
        self._headers = headers
    
    def setReferer( self, referer ):
        self._headers[ 'Referer' ] = referer
    
    def setCookie( self , c ):
        '''
        @parameter cookie: A cookie object as defined in core.data.dc.cookie, or a string.
        '''
        if isinstance( c, cookie):
            self._cookie = c
        elif isinstance( c, basestring ):
            self._cookie = cookie( c )
        elif c == None:
            self._cookie = None
        else:
            om.out.error('[fuzzableRequest error] setCookie received: "' + str(type(c)) + '" , "' + repr(c) + '"'  )
            raise w3afException('Invalid call to fuzzableRequest.setCookie()')
            
    def getURL( self ):
        return self._url
    
    def getURI( self ):
        return self._uri
        
    def setData( self, d ):
        '''
        The data is the string representation of the dataContainer, in most cases it wont be set.
        '''
        self._data = d
        
    def getData( self ):
        '''
        The data is the string representation of the dataContainer, in most cases it will be used as the POSTDATA for requests.
        Sometimes it is also used as the query string data.
        '''
        return self._data
        
    def getMethod( self ):
        return self._method
        
    def getDc( self ):
        return self._dc
        
    def getHeaders( self ):
        return self._headers
    
    def getReferer( self ):
        if 'Referer' in self._fuzzable['headers']:
            return self._headers['Referer']
        return ''
    
    def getCookie( self ):
        if self._cookie:
            return self._cookie
        else:
            return None
    
    def getFileVariables( self ):
        return None
    
    def copy( self ):
        newFr = copy.deepcopy( self )
        return newFr

    def __repr__( self ):
        return '<fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
