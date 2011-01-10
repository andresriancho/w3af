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
from core.data.bloomfilter.pybloom import ScalableBloomFilter

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
        # User configured variables
        self._only_target_domain = True
        self._already_inspected = ScalableBloomFilter()

    def grep(self, request, response):
        '''
        Plugin entry point, get the emails and save them to the kb.
        
        @parameter request: The HTTP request
        @parameter request: The HTTP response
        @return: None
        '''
        uri = response.getURI()
        if uri not in self._already_inspected:
            self._already_inspected.add(uri)
            self._grep_worker(request, response, 'mails', \
                    urlParser.getRootDomain(response.getURL()))
    
            if not self._only_target_domain:
                self._grep_worker(request, response, 'external_mails')
            
    def _grep_worker(self, request, response, kb_key, domain=None):
        '''
        Helper method for using in self.grep()
        
        @parameter request: The HTTP request
        @parameter request: The HTTP response
        @parameter kb_key: Knowledge base dict key
        @parameter domain: Target domain for getEmails filter
        @return: None
        '''
        # Modified when I added the pdfParser
        #if isTextOrHtml(response.getHeaders()):
        try:
            dp = dpCache.dpc.getDocumentParserFor( response )
        except w3afException:
            msg = 'If I can\'t parse the document, I won\'t be able to find any emails.'
            msg += ' Ignoring the response for "' + response.getURL() + '".'
            om.out.debug( msg )
            return

        mails = dp.getEmails(domain)
        
        for mail_address in mails:
            # Reduce false positives
            if request.sent( mail_address ):
                continue
                
            # Email address are case insensitive
            mail_address = mail_address.lower()
            url = response.getURL()

            email_map = {}
            for info_obj in kb.kb.getData( 'mails', 'mails'):
                mail_string = info_obj['mail']
                email_map[ mail_string ] = info_obj

            if mail_address not in email_map:
                # Create a new info object, and report it
                i = info.info()
                i.setPluginName(self.getName())
                i.setURL(url)
                i.setId( response.id )
                i.setName( mail_address )
                desc = 'The mail account: "'+ mail_address + '" was found in: '
                desc += '\n- ' + url
                desc += ' - In request with id: '+ str(response.id)
                i.setDesc( desc )
                i['mail'] = mail_address
                i['url_list'] = [url]
                i['user'] = mail_address.split('@')[0]
                i.addToHighlight( mail_address )
                kb.kb.append( 'mails', kb_key, i )
            
            else:
            
                # Get the corresponding info object.
                i = email_map[ mail_address ]
                # And work
                if url not in i['url_list']:
                    # This email was already found in some other URL
                    # I'm just going to modify the url_list and the description message
                    # of the information object.
                    id_list_of_info = i.getId()
                    id_list_of_info.append( response.id )
                    i.setId( id_list_of_info )
                    i.setURL('')
                    desc = i.getDesc()
                    desc += '\n- ' + url
                    desc += ' - In request with id: '+ str(response.id)
                    i.setDesc( desc )
                    i['url_list'].append(url)
        
    def setOptions( self, optionsMap ):
        self._only_target_domain = optionsMap['onlyTargetDomain'].getValue()
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        d1 = 'When greping, only search mails for domain of target'
        o1 = option('onlyTargetDomain', self._only_target_domain, d1, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'mails', 'mails' ), None )
        self.printUniq( kb.kb.getData( 'mails', 'external_mails' ), None )
    
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
