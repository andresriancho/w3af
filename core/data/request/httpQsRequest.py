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
import core.data.parsers.urlParser as urlParser

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
        url = urlParser.uri2url( url )
        self._url = url.replace(' ', '%20')
        self._uri = self._url
    
    def setURI( self, uri ):
        self._dc = urlParser.getQueryString(uri)
        self._uri = uri.replace(' ', '%20')
        self._url = urlParser.uri2url( uri )
        
    def getURI( self ):
        if self._dc:
            res = self._url + '?' + str(self._dc)
        else:
            res = self._url
        return res
    
    def setData( self, d=None ):
        pass
        
    def getData( self ):
        # The postdata
        return None
    
    def __repr__( self ):
        return '<QS fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
