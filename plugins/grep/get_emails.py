'''
get_emails.py

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
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.parsers.dpCache as dpCache
import core.controllers.outputManager as om

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.w3afException import w3afException
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class get_emails(GrepPlugin):
    '''
    Find email accounts.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        self._already_inspected = scalable_bloomfilter()
        
        # User configured variables
        self._only_target_domain = True

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
            
            self._grep_worker(request, response, 'emails', response.getURL().getRootDomain() )
    
            if not self._only_target_domain:
                self._grep_worker(request, response, 'external_emails')
            
    def _grep_worker(self, request, response, kb_key, domain=None):
        '''
        Helper method for using in self.grep()
        
        @parameter request: The HTTP request
        @parameter response: The HTTP response
        @parameter kb_key: Knowledge base dict key
        @parameter domain: Target domain for getEmails filter
        @return: None
        '''
        try:
            dp = dpCache.dpc.getDocumentParserFor( response )
        except w3afException:
            msg = 'If I can\'t parse the document, I won\'t be able to find any'
            msg += ' emails. Ignoring the response for "%s".'
            om.out.debug( msg % response.getURL() )
            return

        emails = dp.getEmails(domain)

        for mail_address in emails:
            # Reduce false positives
            if request.sent( mail_address ):
                continue
                
            # Email address are case insensitive
            mail_address = mail_address.lower()
            url = response.getURL()

            email_map = {}
            for info_obj in kb.kb.get( 'emails', 'emails'):
                mail_string = info_obj['mail']
                email_map[ mail_string ] = info_obj

            if mail_address not in email_map:
                # Create a new info object, and report it
                i = info.info()
                i.setPluginName(self.get_name())
                i.setURL(url)
                i.set_id( response.id )
                i.set_name( mail_address )
                desc = 'The mail account: "'+ mail_address + '" was found in: '
                desc += '\n- ' + url
                desc += ' - In request with id: '+ str(response.id)
                i.set_desc( desc )
                i['mail'] = mail_address
                i['url_list'] = [url]
                i['user'] = mail_address.split('@')[0]
                i.addToHighlight( mail_address )
                kb.kb.append( 'emails', kb_key, i )
            
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
                    i.set_id( id_list_of_info )
                    i.setURL( url )
                    desc = i.get_desc()
                    desc += '\n- ' + url
                    desc += ' - In request with id: '+ str(response.id)
                    i.set_desc( desc )
                    i['url_list'].append(url)
        
    def set_options( self, options_list ):
        self._only_target_domain = options_list['onlyTargetDomain'].get_value()
    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = OptionList()

        d1 = 'When greping, only search emails for domain of target'
        o1 = opt_factory('onlyTargetDomain', self._only_target_domain, d1, 'boolean')
        ol.add(o1)
        
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'emails', 'emails' ), None )
        self.print_uniq( kb.kb.get( 'emails', 'external_emails' ), None )
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for emails, these can be used in other places,
        like bruteforce plugins, and are of great value when doing a complete
        penetration test.
        '''
