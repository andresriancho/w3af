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
        self._common_http_codes = self._getCommonHTTPCodes()

    def grep(self, request, response):
        '''
        Plugin entry point. Analyze if the HTTP response codes are strange.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        
        Init
        >>> from core.data.url.httpResponse import httpResponse
        >>> from core.data.request.fuzzableRequest import fuzzableRequest
        >>> from core.data.parsers.urlParser import url_object
        >>> from core.controllers.coreHelpers.fingerprint_404 import fingerprint_404_singleton
        >>> f = fingerprint_404_singleton( [False, False, False] )

        Many quick tests:
        >>> body = ''
        >>> url = url_object('http://www.w3af.com/')
        >>> headers = {'content-type': 'text/html'}
        >>> resp_200 = httpResponse(200, body , headers, url, url)
        >>> resp_999 = httpResponse(999, body , headers, url, url)
        >>> resp_123 = httpResponse(123, body , headers, url, url)
        >>> resp_567 = httpResponse(567, body , headers, url, url)
        >>> resp_666 = httpResponse(666, body , headers, url, url)
        >>> resp_777 = httpResponse(777, body , headers, url, url)
        >>> resp_404 = httpResponse(404, body , headers, url, url)
        >>> request = fuzzableRequest()
        >>> request.setURL(url)
        >>> request.setMethod('GET')
        >>> s = strangeHTTPCode()

        >>> s.grep(request, resp_200)
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        0
        >>> kb.kb.cleanup()

        >>> s.grep(request, resp_999)
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        1
        >>> kb.kb.cleanup()

        >>> s.grep(request, resp_123)
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        1
        >>> kb.kb.cleanup()
        
        >>> s.grep(request, resp_567)
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        1
        >>> kb.kb.cleanup()

        >>> s.grep(request, resp_666)
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        1
        >>> kb.kb.cleanup()

        >>> s.grep(request, resp_777)
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        1
        >>> kb.kb.cleanup()
        
        >>> resp_777 = httpResponse(777, body , headers, url, url, id=1)
        >>> s.grep(request, resp_777)
        >>> resp_777 = httpResponse(777, body , headers, url, url, id=2)
        >>> s.grep(request, resp_777)        
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        1
        >>> kb.kb.cleanup()

        >>> s.grep(request, resp_404)
        >>> len(kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode'))
        0
        >>> kb.kb.cleanup()
        
        '''
        if response.getCode() not in self._common_http_codes:
            
            # I check if the kb already has a info object with this code:
            strange_code_infos = kb.kb.getData('strangeHTTPCode', 'strangeHTTPCode')
            
            corresponding_info = None
            for info_obj in strange_code_infos:
                if info_obj['code'] == response.getCode():
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
                i.setName('Strange HTTP Response code - ' + str(response.getCode()))
                i.setURL( response.getURL() )
                i.setId( response.id )
                i['code'] = response.getCode()
                desc = 'The remote Web server sent a strange HTTP response code: "'
                desc += str(response.getCode()) + '" with the message: "'+response.getMsg()
                desc += '", manual inspection is advised.'
                i.setDesc( desc )
                i.addToHighlight( str(response.getCode()), response.getMsg() )
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
