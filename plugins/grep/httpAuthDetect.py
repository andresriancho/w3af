'''
httpAuthDetect.py

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
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import re
from core.data.getResponseType import *
import core.data.constants.severity as severity

class httpAuthDetect(baseGrepPlugin):
    '''
    Find responses that indicate that the resource requires auth.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._authUriRegexStr = '.*://.*?:.*?@[\w\.]{3,40}'

    def _testResponse(self, request, response):
        
        # If I have a 401 code, and this URL wasn't already reported...
        if response.getCode() == 401 and \
        response.getURL() not in [ u.getURL() for u in kb.kb.getData( self , 'auth')]:
            wwwAuth = ''
            for key in response.getHeaders():
                if key.lower() == 'www-authenticate':
                    wwwAuth = response.getHeaders()[ key ]
            
            i = info.info()
            if 'ntlm' in wwwAuth.lower():
                i.setName('NTLM authentication')
            else:
                i.setName('HTTP Basic authentication')
            i.setURL( response.getURL() )
            i.setId( response.id )
            i.setDesc( 'The resource: '+ response.getURL() + ' requires authentication.' +
            ' The message is: ' + wwwAuth + ' .')
            i['message'] = wwwAuth
            
            kb.kb.append( self , 'auth' , i )
            om.out.information( i.getDesc() )
            
        else:
            if re.match( self._authUriRegexStr , response.getURI() ):
                # An authentication URI was found!
                
                v = vuln.vuln()
                v.setURL( response.getURL() )
                v.setId( response.id )
                v.setDesc( 'The resource: '+ response.getURI() + ' has a user and password in the URI .')
                v.setSeverity(severity.HIGH)
                v.setName( 'Basic HTTP credentials' )
                
                kb.kb.append( self , 'userPassUri' , v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                
            # I also search for authentication URI's in the body
            # I know that by doing this I loose the chance of finding hashes in PDF files, but...
            # This is much faster
            if isTextOrHtml( response.getHeaders() ):
                for authURI in re.findall( self._authUriRegexStr , response.getBody() ):
                    v = vuln.vuln()
                    v.setURL( response.getURL() )
                    v.setId( response.id )
                    v.setDesc( 'The resource: '+ response.getURL() + ' has a user and password in the body. The offending URL is: "' + authURI + '".')
                    
                    v.setSeverity(severity.HIGH)
                    v.setName( 'Basic HTTP credentials' )
                    
                    kb.kb.append( self , 'userPassUri' , v )
                    om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
            
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

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
        This plugin greps every page and finds responses that indicate that the resource requires
        authentication.
        '''
