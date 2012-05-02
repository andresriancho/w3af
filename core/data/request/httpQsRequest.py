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
from core.data.request.fuzzableRequest import fuzzableRequest


class HTTPQSRequest(fuzzableRequest):
    '''
    This class represents a fuzzable request that sends all variables
    in the querystring. This is tipically used for GET requests.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, uri, method='GET', headers=None, cookie=None):
        super(HTTPQSRequest, self).__init__(uri, method, headers, cookie)
        
    def setURI(self, uri):
        '''
        >>> r = HTTPQSRequest('http://www.w3af.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: The "uri" parameter of a HTTPQSRequest must be of urlParser.url_object type.
        >>> from core.data.parsers.urlParser import url_object
        >>> r = HTTPQSRequest(url_object('http://www.w3af.com/'))
        >>> uri = url_object('http://www.w3af.com/scan')
        >>> r.setURI(uri)
        >>> r.getURI() == uri
        True
        '''
        super(HTTPQSRequest, self).setURI(uri)
        self._dc = self._uri.querystring
        
    def getURI(self):
        uri = self._url.copy()
        if self._dc:
            uri.querystring = self._dc
        return uri
    
    def setData(self, d):
        pass
    
    def setMethod(self, meth):
        pass
        
    def getData(self):
        # The postdata
        return None
    
    def __repr__(self):
        return ('<QS fuzzable request | %s | %s>' % 
                (self.getMethod(), self.getURI()))