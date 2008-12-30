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
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException


class getMails(baseGrepPlugin):
    '''
    Find email accounts.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

    def _testResponse(self, request, response):
        '''
        Plugin entry point, get the emails and save them to the kb.
        @return: None
        '''
        
        # Modified when I added the pdfParser
        #if isTextOrHtml(response.getHeaders()):
        try:
            dp = dpCache.dpc.getDocumentParserFor( response )
        except w3afException:
            msg = 'If I can\'t parse the document, I won\'t be able to find any emails.'
            msg += ' Ignoring the desponse for "' + response.getURL() + '".'
            om.out.debug( msg )
        else:
            mails = dp.getEmails( urlParser.getRootDomain(response.getURL()) )
            
            for m in mails:
                was_sent = self._wasSent( request, m )
                
                email_url = [ (i['mail'], i.getURL()) for i in  kb.kb.getData( 'mails', 'mails')]
                already_reported = (m, response.getURL()) in email_url
                
                if not was_sent and not already_reported:
                    i = info.info()
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.setName( m )
                    desc = 'The mail account: "'+ m + '" was found in: "' + response.getURL() + '"'
                    i.setDesc( desc )
                    i['mail'] = m
                    i['user'] = m.split('@')[0]
                
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
        self.printUniq( kb.kb.getData( 'mails', 'mails' ), None )
    
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
