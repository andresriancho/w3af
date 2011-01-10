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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.bloomfilter.pybloom import ScalableBloomFilter

import re


class dotNetEventValidation(baseGrepPlugin):
    '''
    Grep every page and identify the ones that have viewstate and don't have event validation.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

        vsRegex = r'<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value=".*?" />'
        self._viewstate = re.compile( vsRegex, re.IGNORECASE|re.DOTALL)
        
        evRegex = r'<input type="hidden" name="__EVENTVALIDATION" '
        evRegex += 'id="__EVENTVALIDATION" value=".*?" />'
        self._eventvalidation = re.compile( evRegex, re.IGNORECASE|re.DOTALL)

        encryptedVsRegex = r'<input type="hidden" name="__VIEWSTATEENCRYPTED" '
        encryptedVsRegex += 'id="__VIEWSTATEENCRYPTED" value=".*?" />'
        self._encryptedVs = re.compile( encryptedVsRegex, re.IGNORECASE|re.DOTALL)

        self._already_reported = ScalableBloomFilter()

    def grep(self, request, response):
        '''
        If I find __VIEWSTATE and empty __EVENTVALIDATION => vuln.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        '''
        if response.is_text_or_html():

            # First verify if we havent greped this yet
            if request.getURI() in self._already_reported:
                return
            else:
                self._already_reported.add(request.getURI())

            res = self._viewstate.search(response.getBody())
            if res:
                # I have __viewstate!, verify if event validation is enabled
                if not self._eventvalidation.search(response.getBody()):
                    # Nice! We found a possible bug =)
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('.NET Event Validation is disabled')
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.addToHighlight(res.group())
                    msg = 'The URL: "' + i.getURL() + '" has .NET Event Validation disabled. '
                    msg += 'This programming/configuration error should be manually verified.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'dotNetEventValidation', i )

                if not self._encryptedVs.search(response.getBody()):
                    # Nice! We can decode the viewstate! =)
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('.NET ViewState encryption is disabled')
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    msg = 'The URL: "' + i.getURL() + '" has .NET ViewState encryption disabled. '
                    msg += 'This programming/configuration error could be exploited '
                    msg += 'to decode the viewstate contents.'
                    i.setDesc( msg )
                    kb.kb.append( self, 'dotNetEventValidation', i )

    
    def setOptions( self, OptionList ):
        '''
        Do nothing, I don't have any options.
        '''
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
