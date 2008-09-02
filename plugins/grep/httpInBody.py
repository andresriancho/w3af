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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import re

class httpInBody (baseGrepPlugin):
    """
    Search for HTTP request/response string in response body.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    """
    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # re that searches for
        #GET / HTTP/1.0
        self._re_request = re.compile('[a-zA-Z] .*? HTTP/1.[01]')
        
        # re that searches for
        #HTTP/1.1 200 OK
        self._re_response = re.compile('HTTP/1.[01] [0-9][0-9][0-9] [a-zA-Z]*')
        
        # re that remove tags
        self._re_removeTags = re.compile('(<.*?>|</.*?>)')
        
    def _testResponse(self, request, response):
        # 501 Code is "Not Implemented" which in some cases responds with this in the body:
        # <body><h2>HTTP/1.1 501 Not Implemented</h2></body>
        # Which creates a false positive.
        if response.getCode() != 501 and response.is_text_or_html():
            
            # First if, mostly for performance.
            # Remember that httpResponse objects have a faster "__in__" than
            # the one in strings; so string in response.getBody() is slower than
            # string in response
            if 'HTTP/1.' in response:
                
                # Now, remove tags
                bodyWithoutTags = self._re_removeTags.sub('', response.getBody() )
                
                if self._re_request.search( bodyWithoutTags ):
                    i = info.info()
                    i.setName('HTTP Request in HTTP body')
                    i.setURI( response.getURI() )
                    i.setId( response.id )
                    i.setDesc( 'A HTTP request was found in the HTTP body of a response' )
                    kb.kb.append( self, 'httpInBody', i )
                    
                if self._re_response.search( bodyWithoutTags ):
                    i = info.info()
                    i.setName('HTTP Response in HTTP body')
                    i.setURI( response.getURI() )
                    i.setId( response.id )
                    i.setDesc( 'A HTTP response was found in the HTTP body of a response' )
                    kb.kb.append( self, 'httpInBody', i )

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
        if kb.kb.getData('httpInBody', 'httpInBody'):
            om.out.information('The following URLs have a HTTP request or response in the HTTP response body:')
            for i in kb.kb.getData('httpInBody', 'httpInBody'):
                om.out.information('- ' + i.getURI() + '  (id:' + str(i.getId()) + ')' )
            
    
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
        This plugin searches for HTTP responses that contain other HTTP request/responses in their response body. This
        situation is mostly seen when programmers enable some kind of debugging for the web application, and print the
        original request in the response HTML as a comment.
        
        No configurable parameters exist.
        '''
