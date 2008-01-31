'''
strangeParameters.py

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

import core.data.parsers.htmlParser as htmlParser
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.parsers.dpCache as dpCache
from core.data.parsers.urlParser import *
import re

class strangeParameters(baseGrepPlugin):
    '''
    Grep the HTML response and find URIs that have strange parameters.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
    def _testResponse(self, request, response):
        
        dp = dpCache.dpc.getDocumentParserFor( response.getBody(), response.getURL() )
        references = dp.getReferences()
        
        for ref in references:
            qs = getQueryString( ref )
            for param in qs:
                if self._isStrange( param, qs[param] ):
                    i = info.info()
                    i.setURI( ref )
                    i.setId( response.id )
                    i.setDesc( 'The URI : ' +  i.getURI() + ' has a parameter named: "' + param + '" with value: "' + qs[param] + '", which is quite odd.' )
                    i.setVar( param )
                    i['parameterValue'] = qs[param]
                    kb.kb.append( self , 'strangeParameters' , i )
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'strangeParameters', 'strangeParameters' ), 'VAR' )

    def _isStrange(self, parameter, value):
        '''
        @return: True if the parameter value is strange
        '''
        self._strangeParameterRegex = []
        # Seems to be a function
        self._strangeParameterRegex.append('\w+\(.*?\)')

        for regex in self._strangeParameterRegex:
            if re.match( regex, value ):
                return True
        
        splittedValue = [ x for x in re.split( r'([a-zA-Z0-9]+)', value ) if x != '' ]
        if len( splittedValue ) > 4:
            return True
        
        return False
        
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
        This plugin greps all responses and tries to identify URIs with strange parameters, some examples of strange
        parameters are:
            - http://a/?b=method(a,c)
            - http://a/?c=x|y|z|d
        '''
