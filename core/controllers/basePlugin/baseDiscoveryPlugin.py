'''
baseDiscoveryPlugin.py

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
from core.controllers.w3afException import w3afException
from core.data.request.frFactory import createFuzzableRequests

class baseDiscoveryPlugin(basePlugin):
    '''
    This is the base class for discovery plugins, all discovery plugins should inherit from it 
    and implement the following methods :
        1. discover(...)
        
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        basePlugin.__init__( self )
        self._urlOpener = None

    def discover_wrapper(self, fuzzable_request):
        '''
        Wrapper around the discover method in order to perform some generic tasks.
        '''
        # I copy the fuzzable request, to avoid cross plugin contamination
        # in other words, if one plugin modified the fuzzable request object
        # INSIDE that plugin, I don't want the next plugin to suffer from that
        fuzzable_request_copy = fuzzable_request.copy()
        self.discover( fuzzable_request_copy )

    def discover(self, fuzzable_request):
        '''
        The url is a string containing the Url to test ( http://somehost.com/foo.php )
        
        This method MUST be implemented on every plugin.
        
        @param url: This is the url to test
        @return: A list :
            1. New Url's found by plugin, could be empty when method ends.
        '''
        raise w3afException('Plugin is not implementing required method discover' )

    def _createFuzzableRequests( self, httpResponse, addSelf=True ):
        return createFuzzableRequests( httpResponse, addSelf )
    
    def getType( self ):
        return 'discovery'
