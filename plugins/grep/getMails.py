'''
getMails.py

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
import core.data.parsers.dpCache as dpCache
from core.data.parsers.urlParser import *
from core.data.getResponseType import *

class getMails(baseGrepPlugin):
    '''
    Find email accounts.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

    def _testResponse(self, request, response):
        
        # Modified when I added the pdfParser
        #if isTextOrHtml(response.getHeaders()):
        dp = dpCache.dpc.getDocumentParserFor( response.getBody(), response.getURL() )
        mails = dp.getAccounts()
        for m in mails:
            if not self._wasSent( request, m ):
                i = info.info()
                i.setURL( response.getURL() )
                i.setId( response.id )
                mail = m + '@' + getDomain( response.getURL() )
                i.setName(mail)
                i.setDesc( 'The mail account: "'+ mail + '" was found in: "' + response.getURL() + '"' )
                i['mail'] = mail
                i['user'] = m
            
                kb.kb.append( 'mails', 'mails', i ) 
                kb.kb.append( self, 'mails', i )
    
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
        self.printUniq( kb.kb.getData( 'getMails', 'mails' ), None )
    
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
        This plugin greps every page for mails, this mails can be later used for bruteforce plugins and are
        of great value when doing a complete penetration test.
        '''
