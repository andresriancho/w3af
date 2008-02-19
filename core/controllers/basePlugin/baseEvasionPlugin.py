'''
baseEvasionPlugin.py

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

class baseEvasionPlugin(basePlugin):
    '''
    This is the base class for evasion plugins, all evasion plugins should inherit from it 
    and implement the following methods :
        1. fuzzUrl(...)
        2. setOptions( OptionList )
        3. getOptionsXML()

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        basePlugin.__init__( self )
        self._urlOpener = None

    def modifyRequest(self, request ):
        '''
        This method mangles the request in order to evade simple IDSs.
        
        This method MUST be implemented on every plugin.
        
        @parameter request: urllib2.Request instance that is going to be modified by the evasion plugin
        @return: A fuzzed version of the Request.
        '''
        raise w3afException('Plugin is not implementing required method modifyRequest' )

    def setUrlOpener(self, foo):
        pass
        
    def getPriority( self ):
        '''
        This function is called when sorting evasion plugins.
        Each evasion plugin should implement this.
        
        @return: An integer specifying the priority. 100 is runned first, 0 last.
        '''
        raise w3afException('Plugin is not implementing required method getPriority' )
    
    def getType( self ):
        return 'evasion'
