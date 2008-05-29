'''
dotNetEventValidation.py

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
from core.data.getResponseType import *
import re

class dotNetEventValidation(baseGrepPlugin):
    '''
    Grep every page and identify the ones that have viewstate and don't have event validation.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

        self._viewstate = re.compile(r'<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value=".*?" />',re.IGNORECASE|re.DOTALL)
        self._eventvalidation = re.compile(r'<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value=".*?" />',re.IGNORECASE|re.DOTALL)

    def _testResponse(self, request, response):
        if isTextOrHtml(response.getHeaders()):
            if self._viewstate.search(response.getBody()):
                # I have __viewstate!, verify if event validation is enabled
                if not self._eventvalidation.search(response.getBody()):
                    # Nice! We found a possible bug =)
                    i = info.info()
                    i.setName('.NET Event Validation is disabled')
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.setDesc( 'The URL: "' + i.getURL() + '" has .NET Event Validation disabled. This programming/configuration error should be manually verified.' )
                    kb.kb.append( self, 'dotNetEventValidation', i )

    
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
        # Print alerts
        self.printUniq( kb.kb.getData( 'dotNetEventValidation', 'dotNetEventValidation' ), 'URL' )
        
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
        ASP.NET implements a method to verify that every postback comes from the corresponding control, which is called EventValidation.
        In some cases the developers disable this kind of verifications by adding EnableEventValidation="false" to the .aspx file header, or
        in the web.config/system.config file.

        This plugin finds pages that have event validation disabled. In some cases, if you analyze the logic of the program and event validation
        is disabled, you'll be able to bypass authorizations or some other controls.
        '''
