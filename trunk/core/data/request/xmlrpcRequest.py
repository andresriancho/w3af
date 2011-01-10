'''
xmlrpcRequest.py

Copyright 2009 Andres Riancho

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
from core.data.parsers.xmlrpc import parse_xmlrpc, build_xmlrpc


class xmlrpcRequest(httpPostDataRequest):
    '''
    This class represents a fuzzable request for a http request that contains XMLRPC postdata.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, original_xmlrpc):
        '''
        @parameter original_xmlrpc: The original XML string that represents the call to the RPC
        '''
        httpPostDataRequest.__init__(self)
        self._original_xmlrpc = original_xmlrpc

    def getData( self ):
        '''
        @return: A string that represents the XMLRPC data saved in the dc.
        '''
        return build_xmlrpc(self._original_xmlrpc, self._dc)
        
    def __str__( self ):
        '''
        Return a str representation of this fuzzable request.
        '''
        res = '[[XMLRPC]] '
        res += self._url
        res += ' | Method: ' + self._method
        res += ' | XMLRPC: ('
        res += ','.join([i[1] for i in parse_xmlrpc(self._original_xmlrpc).all_parameters ])
        res += ')'
        return res
    
    def setDc( self , data_container ):
        self._dc = data_container
            
    def __repr__( self ):
        return '<XMLRPC fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
