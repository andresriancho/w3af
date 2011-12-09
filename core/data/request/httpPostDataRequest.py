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

from itertools import imap

from core.controllers.misc.io import is_file_like
from core.data.request.fuzzableRequest import fuzzableRequest


class httpPostDataRequest(fuzzableRequest):
    '''
    This class represents a fuzzable request that sends all variables in the
    POSTDATA. This is typically used for POST requests.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, uri, method='POST', headers=None,
                 cookie=None, dc=None, files=None):
        fuzzableRequest.__init__(self, uri, method, headers, cookie, dc)
        self._files = files or []

    def getData(self):
        '''
        @return: A string representation of the dataContainer. There is a
        special case, in which the dataContainer has a file inside, in which
        we return the data container as it is. This is needed by the multipart
        post handler.
        '''

        # TODO: This is a hack I'm not comfortable with. There should
        # be a fancier way to do this.
        # If it contains a file then we are not interested on returning
        # its string representation
        for value in self._dc.itervalues():
            
            if isinstance(value, basestring):
                continue
            elif is_file_like(value) or (hasattr(value, "__iter__") and \
                   any(imap(is_file_like, value))):
                return self._dc
        
        # Ok, no file was found; return the string representation
        return str(self._dc)
        
    def setFileVariables( self, file_variables ):
        '''
        @parameter file_variables: A list of postdata parameters that contain
            a file
        '''
        self._files = file_variables
    
    def getFileVariables( self ):
        '''
        @return: A list of postdata parameters that contain a file
        '''
        return self._files
    
    def __repr__( self ):
        return '<postdata fuzzable request | %s | %s>' % \
                    (self.getMethod(), self.getURI())
    
