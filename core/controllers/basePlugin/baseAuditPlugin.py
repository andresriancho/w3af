'''
baseAuditPlugin.py

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
from core.controllers.basePlugin.basePlugin import basePlugin
import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser

class baseAuditPlugin(basePlugin):
    '''
    This is the base class for audit plugins, all audit plugins should inherit from it 
    and implement the following methods :
        1. _fuzzRequests(...)
        
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        basePlugin.__init__( self )
        self._urlOpener = None

    def audit( self, fuzzableRequest ):
        '''
        Receives a fuzzableRequest and forwards it to the internal method
        _fuzzRequests()
        
        @parameter fuzzableRequest: A fuzzableRequest instance
        '''
        self._fuzzRequests( fuzzableRequest )
        
    def _fuzzRequests( self, freq ):
        '''
        The freq is a fuzzableRequest that is going to be modified and sent.
        
        This method MUST be implemented on every plugin.
        
        @param freq: A fuzzableRequest
        '''
        raise w3afException('Plugin is not implementing required method _fuzzRequests' )
    
    def _analyzeResult( self, mutant, res ):
        '''
        This method analyzes the result of _sendMutant().
        
        This method MUST be implemented on every plugin.
        
        @param mutant: The mutant that was sent using _sendMutant
        @param res: The response of _sendMutant
        '''
        raise w3afException('Plugin is not implementing required method _analyzeResult' )

    def _hasNoBug( self, plugin, kbVar, uri, variable ):
        '''
        Verify if a variable name has a reported sql injection vuln ( in the kb ).
        @parameter uri: The uri where we should search for bugs.
        @parameter variable: The variable that is queryed for bugs.
        @return: True if the variable HAS a reported bug.
        '''
        vuln = kb.kb.getData( plugin , kbVar )
        url = urlParser.uri2url( uri )
        res = True
        for v in vuln:
            if v.getVar() == variable and urlParser.uri2url( v.getURL() ) == url:
                res = False
                break
        return res
        
    def getType( self ):
        return 'audit'
