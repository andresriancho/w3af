'''
strangeHTTPCode.py

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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info


class strangeHTTPCode(baseGrepPlugin):
    '''
    Analyze HTTP response codes sent by the remote web application.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._commonCodes = self._getCommonHTTPCodes()

    def _testResponse(self, request, response):
        
        if response.getCode() not in self._commonCodes:
            i = info.info()
            i.setName('Strange HTTP Response code - ' + str(response.getCode()))
            i.setURL( response.getURL() )
            i.setId( response.id )
            desc = 'The URL: "' +  i.getURL() + '" sent a strange HTTP response code: "'
            desc += str(response.getCode()) + '" with the message: "'+response.getMsg()
            desc += '", manual inspection is adviced.'
            i.setDesc( desc )
            kb.kb.append( self , 'strangeHTTPCode' , i )
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'strangeHTTPCode', 'strangeHTTPCode' ), 'URL' )
        
    def _getCommonHTTPCodes(self):
        codes = []
        codes.extend([200, ])
        codes.extend([301, 302, 303])
        codes.extend([401, 403, 404])
        codes.extend([500, 501])
        return codes

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Analyze HTTP response codes sent by the remote web application and report uncommon findings.
        '''
