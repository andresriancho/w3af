''''
httpInBody.py

Copyright 2008 Andres Riancho

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
from core.data.esmre.multi_re import multi_re

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info


class httpInBody (baseGrepPlugin):
    """
    Search for HTTP request/response string in response body.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    """

    HTTP = (
            # GET / HTTP/1.0
            ('[a-zA-Z]{3,6} .*? HTTP/1.[01]', 'REQUEST'),
            # HTTP/1.1 200 OK
            ('HTTP/1.[01] [0-9][0-9][0-9] [a-zA-Z]*', 'RESPONSE')
    )
    _multi_re = multi_re( HTTP )
    

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._already_inspected = scalable_bloomfilter()
                        
    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        uri = response.getURI()
        # 501 Code is "Not Implemented" which in some cases responds with this in the body:
        # <body><h2>HTTP/1.1 501 Not Implemented</h2></body>
        # Which creates a false positive.
        if response.getCode() != 501 and uri not in self._already_inspected \
        and response.is_text_or_html():
            # Don't repeat URLs
            self._already_inspected.add(uri)

            body_without_tags = response.getClearTextBody()
            if body_without_tags is None:
                return
            
            for match, _, _, reqres in self._multi_re.query( body_without_tags ):

                if reqres == 'REQUEST':            
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('HTTP Request in HTTP body')
                    i.setURI(uri)
                    i.setId(response.id)
                    i.setDesc('An HTTP request was found in the HTTP body of a response')
                    i.addToHighlight(match.group(0))
                    kb.kb.append(self, 'request', i)

                if reqres == 'RESPONSE':                    
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('HTTP Response in HTTP body')
                    i.setURI(uri)
                    i.setId(response.id)
                    i.setDesc('An HTTP response was found in the HTTP body of a response')
                    i.addToHighlight(match.group(0))
                    kb.kb.append(self, 'response', i)

    def setOptions( self, optionsMap ):
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
        for info_type in ['request', 'response']:
            
            if kb.kb.getData('httpInBody', info_type):
                msg = 'The following URLs have an HTTP '+ info_type +' in the HTTP response body:'
                om.out.information(msg)
                for i in kb.kb.getData('httpInBody', info_type):
                    om.out.information('- ' + i.getURI() + '  (id:' + str(i.getId()) + ')' )
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for HTTP responses that contain other HTTP request/responses
        in their response body. This situation is mostly seen when programmers enable
        some kind of debugging for the web application, and print the original request
        in the response HTML as a comment.
        
        No configurable parameters exist.
        '''
