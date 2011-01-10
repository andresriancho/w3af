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
        self._common_headers = self._getCommonHeaders()

    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''

        # Check if the header names are common or not
        for header_name in response.getHeaders().keys():
            if header_name.upper() not in self._common_headers:
                
                # I check if the kb already has a info object with this code:
                strange_header_infos = kb.kb.getData('strangeHeaders', 'strangeHeaders')
                
                corresponding_info = None
                for info_obj in strange_header_infos:
                    if info_obj['header_name'] == header_name:
                        corresponding_info = info_obj
                        break
                
                if corresponding_info:
                    # Work with the "old" info object:
                    id_list = corresponding_info.getId()
                    id_list.append( response.id )
                    corresponding_info.setId( id_list )
                else:
                    # Create a new info object from scratch and save it to the kb:
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Strange header')
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    msg = 'The remote web server sent the HTTP header: "' + header_name
                    msg += '" with value: "' + response.getHeaders()[header_name] + '".'
                    i.setDesc( msg )
                    i['header_name'] = header_name
                    hvalue = response.getHeaders()[header_name]
                    i['header_value'] = hvalue
                    i.addToHighlight( hvalue, header_name )
                    kb.kb.append( self , 'strangeHeaders' , i )


        # Now check for protocol anomalies
        self._content_location_not_300(request, response)

    def _content_location_not_300( self, request, response):
        '''
        Check if the response has a content-location header and the response code
        is not in the 300 range.
        
        @return: None, all results are saved in the kb.
        '''
        if 'content-location' in response.getLowerCaseHeaders() \
        and response.getCode() not in xrange(300,310):
            i = info.info()
            i.setPluginName(self.getName())
            i.setName('Content-Location HTTP header anomaly')
            i.setURL( response.getURL() )
            i.setId( response.id )
            msg = 'The URL: "' +  i.getURL() + '" sent the HTTP header: "content-location"' 
            msg += ' with value: "' + response.getLowerCaseHeaders()['content-location']
            msg += '" in an HTTP response with code ' + str(response.getCode()) + ' which is'
            msg += ' a violation to the RFC.'
            i.setDesc( msg )
            i.addToHighlight( 'content-location' )
            kb.kb.append( self , 'anomaly' , i )

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
        #i['header_name'] = header_name
        #i['header_value'] = response.getHeaders()[header_name]
        
        # Group correctly
        tmp = []
        for i in headers:
            tmp.append( (i['header_name'], i.getURL() ) )
        
        # And don't print duplicates
        tmp = list(set(tmp))
        
        resDict, itemIndex = groupbyMinKey( tmp )
        if itemIndex == 0:
            # Grouped by header_name
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
        headers.append("ACCEPT-RANGES")
        headers.append("AGE")
        headers.append("ALLOW")
        headers.append("CONNECTION")
        headers.append("CONTENT-LENGTH")
        headers.append("CONTENT-TYPE")
        headers.append("CONTENT-LANGUAGE")
        headers.append("CONTENT-LOCATION")
        headers.append("CACHE-CONTROL")
        headers.append("DATE")
        headers.append("EXPIRES")
        headers.append("ETAG")
        headers.append("KEEP-ALIVE")
        headers.append("LAST-MODIFIED")
        headers.append("LOCATION")
        headers.append("PUBLIC")
        headers.append("PRAGMA")
        headers.append("PROXY-CONNECTION")
        headers.append("SET-COOKIE")    
        headers.append("SERVER")
        headers.append("TRANSFER-ENCODING")
        headers.append("VIA")        
        headers.append("VARY")
        headers.append("WWW-AUTHENTICATE")
        headers.append("X-POWERED-BY")
        headers.append("X-ASPNET-VERSION")
        headers.append("X-CACHE")
        headers.append("X-PAD")
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
