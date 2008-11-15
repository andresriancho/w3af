'''
httpPostDataRequest.py

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
import core.data.dc.dataContainer as dc

class httpPostDataRequest(fuzzableRequest):
    '''
    This class represents a fuzzable request that sends all variables in the POSTDATA. This is tipically used
    for POST requests.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        fuzzableRequest.__init__(self)
        self._method = 'POST'
        self._files = []

    def getData( self ):
        return str( self._dc )
        
    def setFileVariables( self, file_variables ):
        '''
        @parameter file_variables: A list of postdata parameters that contain a file
        '''
        self._files = file_variables
    
    def getFileVariables( self ):
        '''
        @return: A list of postdata parameters that contain a file
        '''
        return self._files
    
    def __repr__( self ):
        return '<postdata fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
