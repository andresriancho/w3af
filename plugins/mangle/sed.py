'''
sed.py

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
from core.controllers.basePlugin.baseManglePlugin import *
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import re
from core.controllers.w3afException import w3afException
from core.data.request.frFactory import createFuzzableRequestRaw

class sed(baseManglePlugin):
    '''
    This plugin is a "stream editor" for http requests and responses.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseManglePlugin.__init__(self)
        self._reqBodyManglers = []
        self._reqHeadManglers = []
        self._resBodyManglers = []
        self._resHeadManglers = []
        
        # User options
        self._userOptionfixContentLen = True
        self._priority = 20
        self._expressions = ''
        
    def mangleRequest(self, request ):
        '''
        This method mangles the request.
        
        @param request: This is the request to mangle.
        @return: A mangled version of the request.
        '''
        data = request.getData()
        for regex,string in self._reqBodyManglers:
            data = regex.sub( string, data )
        
        headerString = headersToString( request.getHeaders() )
        for regex,string in self._reqHeadManglers:
            headerString = regex.sub( string, headerString )
        headerDict = stringToHeaders( headerString )
        
        request = createFuzzableRequestRaw( request.getMethod() , request.getURL(), data, headerDict )
        
        return request
    
    def mangleResponse(self, response ):
        '''
        This method mangles the response.
        
        @param response: This is the response to mangle.
        @return: A mangled version of the response.
        '''
        body = response.getBody()
        for regex,string in self._resBodyManglers:
            body = regex.sub( string, response.getBody() )
        response.setBody( body )
        
        headerString = headersToString( response.getHeaders() )
        for regex,string in self._resHeadManglers:
            headerString = regex.sub( string, headerString )
        headerDict = stringToHeaders( headerString )
        response.setHeaders( headerDict )
        
        if len( self._resBodyManglers ) != 0 and self._userOptionfixContentLen :
            response = self._fixContentLen( response )
        
        return response
    
    def setOptions( self, OptionList ):
        
        self._userOptionfixContentLen = OptionList['fixContentLen'].getValue()
        self._priority = OptionList['priority'].getValue()
        
        if 'expressions' in OptionList.keys(): 
            self._expressions = ','.join( OptionList['expressions'].getValue() )
            self._expressions = re.findall( '([qs])([bh])/(.*?)/(.*?)/;?' , self._expressions )
            
            if len( self._expressions ) == 0 and len ( OptionList['expressions'].getValue() ) != 0:
                raise w3afException('The user specified expression is invalid.')
            
            for exp in self._expressions:
                if exp[0] not in ['q','s']:
                    raise w3afException('The first letter of the sed expression should be q(reQuest) or s(reSponse).')
                
                if exp[1] not in ['b','h']:
                    raise w3afException('The second letter of the sed expression should be b(body) or h(header).')
                
                try:
                    regex = re.compile( exp[2] )
                except:
                    raise w3afException('Invalid regular expression in sed plugin.')
                    
                if exp[0] == 'q':
                    # The expression mangles the request
                    if exp[1] == 'b':
                        self._reqBodyManglers.append( (regex, exp[3]) )
                    else:
                        self._reqHeadManglers.append( (regex, exp[3]) )
                else:
                    # The expression mangles the response
                    if exp[1] == 'b':
                        self._resBodyManglers.append( (regex, exp[3]) )
                    else:
                        self._resHeadManglers.append( (regex, exp[3]) )

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Stream edition expressions'
        h1 = 'Stream edition expressions are strings that tell the sed plugin what to change. Sed plugin uses regular expressions, some examples: \n - qh/User/NotLuser/ ; This will make sed search in the the re[q]uest [h]eader for the string User and replace it with NotLuser.\n - sb/[fF]orm/form ; This will make sed search in the re[s]ponse [b]ody for the strings form or Form and replace it with form. Multiple expressions can be specified separated by commas.'
        o1 = option('expressions', self._expressions, d1, 'list', help=h1)
        
        d2 = 'Fix the content length header after mangling'
        o2 = option('fixContentLen', self._fixContentLen, d2, 'boolean')

        d3 = 'Plugin execution priority'
        h3 = 'Mangle plugins are ordered using the priority parameter'
        o3 = option('priority', self._priority, d3, 'integer', help=h3)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        return ol
  
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getPriority( self ):
        return self._priority
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin is a stream editor for web requests and responses.
        
        Three configurable parameters exist:
            - priority
            - expressions
            - fixContentLen
        
        Stream edition expressions are strings that tell the sed plugin what to change. Sed plugin uses regular expressions, 
        some examples:
            - qh/User/NotLuser/ ; This will make sed search in the the re[q]uest [h]eader for the string User and replace it with NotLuser.
            - sb/[fF]orm/form ; This will make sed search in the re[s]ponse [b]ody for the strings form or Form and replace it with form. 
        Multiple expressions can be specified separated by commas.
        '''
