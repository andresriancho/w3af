'''
jsonPostDataRequest.py

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
from core.data.request.httpPostDataRequest import httpPostDataRequest
import core.data.dc.dataContainer as dc
try:
    import extlib.simplejson as json
except:
    import simplejson as json

class jsonPostDataRequest(httpPostDataRequest):
    '''
    This class represents a fuzzable request for a http request that contains JSON postdata.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        httpPostDataRequest.__init__(self)

    def getData( self ):
        '''
        @return: A string that represents the JSON data saved in the dc.
        '''
        res = json.dumps(self._dc)
        return res
        
    def __str__( self ):
        '''
        Return a str representation of this fuzzable request.
        '''
        strRes = '[[JSON]] '
        strRes += self._url
        strRes += ' | Method: ' + self._method
        strRes += ' | JSON: ('
        strRes += json.dumps(self._dc)
        strRes += ')'
        return strRes
    
    def setDc( self , dataCont ):
        self._dc = dataCont
            
    def __repr__( self ):
        return '<JSON fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
