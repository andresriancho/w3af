'''
httpQsRequest.py

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
from core.data.request.fuzzableRequest import fuzzableRequest
from core.data.parsers.urlParser import url_object


class httpQsRequest(fuzzableRequest):
    '''
    This class represents a fuzzable request that sends all variables in the querystring. This is tipically used
    for GET requests.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        fuzzableRequest.__init__(self)
        self._method = 'GET'
    
    def setURL( self , url ):
        '''
        >>> r = httpQsRequest()
        >>> r.setURL('http://www.google.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The URL of a httpQsRequest must be of urlParser.url_object type.
        >>> r = httpQsRequest()
        >>> r.setURL( url_object('http://www.google.com/') )
        >>>
        '''
        if not isinstance(url, url_object):
            raise ValueError('The URL of a httpQsRequest must be of urlParser.url_object type.')
        
        self._url = url.uri2url()
        self._uri = url
    
    def setURI( self, uri ):
        '''
        >>> r = httpQsRequest()
        >>> r.setURI('http://www.google.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The URI of a httpQsRequest must be of urlParser.url_object type.
        >>> r = httpQsRequest()
        >>> r.setURI( url_object('http://www.google.com/') )
        >>>
        '''
        if not isinstance(uri, url_object):
            raise ValueError('The URI of a httpQsRequest must be of urlParser.url_object type.')
        
        self._dc = uri.getQueryString()
        self._uri = uri
        self._url = uri.uri2url()
        
    def getURI( self ):
        if self._dc:
            res = self._url.copy()
            res.setQueryString( self._dc )
        else:
            res = self._url.copy()
        return res
    
    def setData( self, d=None ):
        pass
        
    def getData( self ):
        # The postdata
        return None
    
    def __repr__( self ):
        return '<QS fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
