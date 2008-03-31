'''
strangeHeaders.py

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
from core.controllers.misc.groupbyMinKey import groupbyMinKey

class strangeHeaders(baseGrepPlugin):
    '''
    Grep headers for uncommon headers sent in HTTP responses.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._commonHeaders = self._getCommonHeaders()

    def _testResponse(self, request, response):
        
        for headerName in response.getHeaders().keys():
            if headerName.upper() not in self._commonHeaders:
                i = info.info()
                i.setName('Strange header')
                i.setURL( response.getURL() )
                i.setId( response.id )
                i.setDesc( 'The URL : ' +  i.getURL() + ' sent the Header: "' + headerName + '" with value: "' + response.getHeaders()[headerName] + '"' )
                i['headerName'] = headerName
                i['headerValue'] = response.getHeaders()[headerName]
                kb.kb.append( self , 'strangeHeaders' , i )
    
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
        headers = kb.kb.getData( 'strangeHeaders', 'strangeHeaders' )
        # This is how I saved the data:
        #i['headerName'] = headerName
        #i['headerValue'] = response.getHeaders()[headerName]
        
        # Group correctly
        tmp = []
        for i in headers:
            tmp.append( (i['headerName'], i.getURL() ) )
        
        # And don't print duplicates
        tmp = list(set(tmp))
        
        resDict, itemIndex = groupbyMinKey( tmp )
        if itemIndex == 0:
            # Grouped by headerName
            msg = 'The header: "%s" was sent by these URLs:'
        else:
            # Grouped by URL
            msg = 'The URL: "%s" sent these strange headers:'
            
        for k in resDict:
            om.out.information(msg % k)
            for i in resDict[k]:
                om.out.information('- ' + i )
        
    def _getCommonHeaders(self):
        headers = []
        ### TODO: verify if I need to add more values here
        # Remember that this headers are only the ones SENT BY THE SERVER TO THE CLIENT
        # Headers must be uppercase in order to compare them
        headers.append("SET-COOKIE")    
        headers.append("SERVER")
        headers.append("CONNECTION")
        headers.append("DATE")
        headers.append("LAST-MODIFIED")
        headers.append("ETAG")
        headers.append("ACCEPT-RANGES")
        headers.append("CONTENT-LENGTH")
        headers.append("CONTENT-TYPE")
        headers.append("X-POWERED-BY")
        headers.append("EXPIRES")
        headers.append("CACHE-CONTROL")
        headers.append("PRAGMA")
        headers.append("PROXY-CONNECTION")
        headers.append("VIA")
        headers.append("KEEP-ALIVE")
        headers.append("ALLOW")
        headers.append("TRANSFER-ENCODING")
        headers.append("CONTENT-LANGUAGE")
        headers.append("VARY")
        headers.append("LOCATION")
        headers.append("PUBLIC")
        headers.append("AGE")
        return headers

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
        This plugin greps all headers for non-common headers. This could be usefull to identify special modules
        and features added to the server.
        '''
