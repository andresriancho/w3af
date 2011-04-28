'''
baseManglePlugin.py

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

from core.controllers.basePlugin.basePlugin import basePlugin
from core.data.request.httpPostDataRequest import httpPostDataRequest
from core.data.request.httpQsRequest import httpQsRequest
from core.controllers.w3afException import *
import core.controllers.outputManager as om


class baseManglePlugin(basePlugin):
    '''
    This is the base class for mangle plugins, all mangle plugins should inherit from it 
    and implement the following methods :
        1. mangleRequest( request )
        2. mangleResponse( request )
        3. setOptions( OptionList )
        4. getOptions()

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def getType( self ):
        return 'mangle'

    def __init__(self):
        pass

    def mangleRequest(self, request ):
        '''
        This method mangles the request.
        
        This method MUST be implemented on every plugin.
        
        @param request: This is the request to mangle.
        @return: A mangled version of the request.
        '''
        raise w3afException('Plugin is not implementing required method mangleRequest' )
    
    def mangleResponse(self, response ):
        '''
        This method mangles the response.
        
        This method MUST be implemented on every plugin.
        
        @param response: This is the response to mangle.
        @return: A mangled version of the response.
        '''
        raise w3afException('Plugin is not implementing required method mangleResponse' )
        
    def setUrlOpener(self, foo):
        pass
        
    def __gt__( self, other ):
        '''
        This function is called when sorting mangle plugins.
        '''
        if self.getPriority() > other.getPriority():
            return True
        else:
            return False
        
    def __lt__( self, other ):
        '''
        This function is called when sorting evasion plugins.
        '''
        return not self.__gt__( other )
    
    def __eq__( self, other ):
        '''
        This function is called when sorting mangle plugins.
        '''
        if self.getPriority() == other.getPriority():
            return True
        else:
            return False
        
    def getPriority( self ):
        '''
        This function is called when sorting mangle plugins.
        Each mangle plugin should implement this.
        
        @return: An integer specifying the priority. 100 is runned first, 0 last.
        '''
        raise w3afException('Plugin is not implementing required method getPriority' )
    
    def _fixContentLen( self, response ):
        '''
        If the content-length header is present, calculate the new len and 
        update the header.
        '''
        cl = 'Content-Length'
        for i in response.getHeaders():
            if i.lower() == 'Content-length'.lower():
                cl = i
                break
        
        headers = response.getHeaders()
        headers[ cl ] = str( len( response.getBody() ) )
        response.setHeaders( headers )
        return response
    
def headersToString( headerDict ):
    '''
    @parameter headerDict: The header dictionary of the request
    @return: A string representation of the dictionary
    '''
    res = ''
    for key in headerDict:
        res += key + ': ' + headerDict[key] + '\r\n'
    return res
    
def stringToHeaders( headerString ):
    '''
    The reverse of headersToString
    '''
    res = {}
    splittedString = headerString.split('\r\n')
    for s in splittedString:
        if s != '':
            try:
                name = s.split(':')[0]
                value = ':'.join( s.split(':')[1:] )
            except:
                om.out.error('You "over-mangled" the header! Now the headers are invalid, ignoring:' + s )
            else:
                res[ name ] = value[1:] # Escape the space after the ":"
    return res
