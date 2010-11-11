'''
baseGrepPlugin.py

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
import core.controllers.outputManager as om
import core.data.kb.config as cf
from core.controllers.w3afException import w3afException

import urllib


class baseGrepPlugin(basePlugin):
    '''
    This is the base class for grep plugins, all grep plugins should inherit from it 
    and implement the following methods :
        1. testResponse(...)
        2. setOptions( OptionList )
        3. getOptions()

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        basePlugin.__init__( self )
        self._urlOpener = None

    def grep_wrapper(self, fuzzableRequest, response):
        '''
        This method tries to find patterns on responses.
        
        This method CAN be implemented on a plugin, but its better to do your searches in _testResponse().
        
        @param response: This is the httpResponse object to test.
        @param fuzzableRequest: This is the fuzzable request object that generated the current response being analyzed.
        @return: If something is found it must be reported to the Output Manager and the KB.
        '''
        if response.getFromCache():
            #om.out.debug('Grep plugins not testing: ' + repr(fuzzableRequest) + ' cause it was already tested.' )
            pass
        elif fuzzableRequest.getURL().getDomain() in cf.cf.getData('targetDomains'):
            self.grep( fuzzableRequest, response )
        else:
            #om.out.debug('Grep plugins not testing: ' + fuzzableRequest.getURL() + ' cause it aint a target domain.' )
            pass
    
    def grep(self, fuzzableRequest, response ):
        '''
        Analyze the response.
        
        @parameter fuzzableRequest: The request that was sent
        @parameter response: The HTTP response obj
        '''
        raise w3afException('Plugin is not implementing required method grep' )
            
    def _testResponse( self, request, response ):
        '''
        This method tries to find patterns on responses.
        
        This method MUST be implemented on every plugin.
        
        @param response: This is the htmlString response to test
        @param request: This is the request object that generated the current response being analyzed.
        @return: If something is found it must be reported to the Output Manager and the KB.
        '''
        raise w3afException('Plugin is not implementing required method _testResponse' )
        
    def setUrlOpener(self, foo):
        pass
        
    def getType( self ):
        return 'grep'
