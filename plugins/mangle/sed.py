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

from core.controllers.basePlugin.baseManglePlugin import baseManglePlugin
from core.controllers.basePlugin.baseManglePlugin import headersToString, stringToHeaders

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
        self._req_body_manglers = []
        self._req_head_manglers = []
        self._res_body_manglers = []
        self._res_head_manglers = []
        
        # User options
        self._user_option_fix_content_len = True
        self._priority = 20
        self._expressions = ''
        
    def mangleRequest(self, request ):
        '''
        This method mangles the request.
        
        @param request: This is the request to mangle.
        @return: A mangled version of the request.
        '''
        data = request.getData()
        for regex, string in self._req_body_manglers:
            data = regex.sub( string, data )
        
        header_string = headersToString( request.getHeaders() )
        for regex, string in self._req_head_manglers:
            header_string = regex.sub( string, header_string )
        header_dict = stringToHeaders( header_string )
        
        request = createFuzzableRequestRaw( request.getMethod() , request.getURL(), 
                                            data, header_dict )
        
        return request
    
    def mangleResponse(self, response ):
        '''
        This method mangles the response.
        
        @param response: This is the response to mangle.
        @return: A mangled version of the response.
        '''
        body = response.getBody()
        for regex, string in self._res_body_manglers:
            body = regex.sub( string, response.getBody() )
        response.setBody( body )
        
        header_string = headersToString( response.getHeaders() )
        for regex, string in self._res_head_manglers:
            header_string = regex.sub( string, header_string )
        header_dict = stringToHeaders( header_string )
        response.setHeaders( header_dict )
        
        if len( self._res_body_manglers ) != 0 and self._user_option_fix_content_len:
            response = self._fixContentLen( response )
        
        return response
    
    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self._user_option_fix_content_len = OptionList['fixContentLen'].getValue()
        self._priority = OptionList['priority'].getValue()
        
        self._expressions = ','.join( OptionList['expressions'].getValue() )
        self._expressions = re.findall( '([qs])([bh])/(.*?)/(.*?)/;?' , self._expressions )
        
        if len( self._expressions ) == 0 and len ( OptionList['expressions'].getValue() ) != 0:
            raise w3afException('The user specified expression is invalid.')
        
        for exp in self._expressions:
            if exp[0] not in ['q', 's']:
                msg = 'The first letter of the sed expression should be q(reQuest) or s(reSponse).'
                raise w3afException( msg )
            
            if exp[1] not in ['b', 'h']:
                msg = 'The second letter of the sed expression should be b(body) or h(header).'
                raise w3afException( msg )
            
            try:
                regex = re.compile( exp[2] )
            except:
                raise w3afException('Invalid regular expression in sed plugin.')
                
            if exp[0] == 'q':
                # The expression mangles the request
                if exp[1] == 'b':
                    self._req_body_manglers.append( (regex, exp[3]) )
                else:
                    self._req_head_manglers.append( (regex, exp[3]) )
            else:
                # The expression mangles the response
                if exp[1] == 'b':
                    self._res_body_manglers.append( (regex, exp[3]) )
                else:
                    self._res_head_manglers.append( (regex, exp[3]) )

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Stream edition expressions'
        h1 = 'Stream edition expressions are strings that tell the sed plugin what to change.'
        h1 += ' Sed plugin uses regular expressions, some examples: \n - qh/User/NotLuser/ ;'
        h1 += ' This will make sed search in the the re[q]uest [h]eader for the string User'
        h1 += ' and replace it with NotLuser.\n - sb/[fF]orm/form ; This will make sed search'
        h1 += ' in the re[s]ponse [b]ody for the strings form or Form and replace it with form.'
        h1 += ' Multiple expressions can be specified separated by commas.'
        o1 = option('expressions', self._expressions, d1, 'list', help=h1)
        
        d2 = 'Fix the content length header after mangling'
        o2 = option('fixContentLen', self._user_option_fix_content_len, d2, 'boolean')

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
        '''
        This function is called when sorting mangle plugins.
        Each mangle plugin should implement this.
        
        @return: An integer specifying the priority. 100 is runned first, 0 last.
        '''        
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
        
        Stream edition expressions are strings that tell the sed plugin what to change. Sed plugin
        uses regular expressions, some examples:
            - qh/User/NotLuser/
                This will make sed search in the the re[q]uest [h]eader for the string User and
                replace it with NotLuser.
                
            - sb/[fF]orm/form
                This will make sed search in the re[s]ponse [b]ody for the strings form or Form
                and replace it with form. 
        
        Multiple expressions can be specified separated by commas.
        '''
