'''
fingerGoogle.py

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

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.searchEngines.googleSearchEngine import googleSearchEngine as google
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
import core.data.parsers.dpCache as dpCache
from core.controllers.w3afException import w3afRunOnce


class fingerGoogle(baseDiscoveryPlugin):
    '''
    Search Google using the Google API to get a list of users for a domain.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._run = True
        self._accounts = []
        
        # User configured 
        self._result_limit = 300
        self._fast_search = False
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                    (among other things) the URL to test.
        '''
        if not self._run:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # This plugin will only run one time. 
            self._run = False
            
            self._google = google(self._urlOpener)
            self._domain = domain = urlParser.getDomain( fuzzableRequest.getURL() )
            self._domain_root = urlParser.getRootDomain( domain )
            
            if self._fast_search:
                self._do_fast_search( domain )
            else:
                self._do_complete_search( domain )
            
            self._tm.join( self )
            self.printUniq( kb.kb.getData( 'fingerGoogle', 'mails' ), None )
            return []

    def _do_fast_search( self, domain ):
        '''
        Only search for mail addresses in the google result page.
        '''
        search_string = '@'+ self._domain_root
        try:
            result_page_objects = self._google.getNResultPages( search_string , self._result_limit )
        except w3afException, w3:
            om.out.error(str(w3))
            # If I found an error, I don't want to be run again
            raise w3afRunOnce()
        else:
            # Happy happy joy, no error here!
            for result in result_page_objects:
                self._parse_document( result )
        
    def _do_complete_search( self, domain ):
        '''
        Performs a complete search for email addresses.
        '''
        search_string = '@'+ self._domain_root
        try:
            result_page_objects = self._google.getNResultPages( search_string , self._result_limit )
        except w3afException, w3:
            om.out.error(str(w3))
            # If I found an error, I don't want to be run again
            raise w3afRunOnce()
        else:
            # Happy happy joy, no error here!
            for result in result_page_objects:
                targs = (result,)
                self._tm.startFunction( target=self._find_accounts, args=targs, ownerObj=self )
            
    def _find_accounts(self, googlePage ):
        '''
        Finds mails in google result page.
        
        @return: A list of valid accounts
        '''
        try:
            om.out.debug('Searching for mails in: ' + googlePage.getURI() )
            if self._domain == urlParser.getDomain( googlePage.getURI() ):
                response = self._urlOpener.GET( googlePage.getURI(), useCache=True, \
                                                                grepResult=True )
            else:
                response = self._urlOpener.GET( googlePage.getURI(), useCache=True, \
                                                                grepResult=False )
        except KeyboardInterrupt, e:
            raise e
        except w3afException, w3:
            msg = 'xUrllib exception raised while fetching page in fingerGoogle,'
            msg += ' error description: ' + str(w3)
            om.out.debug( msg )
            self._newAccounts = []
        else:
            self._parse_document( response )
            
    def _parse_document( self, response ):
        '''
        Parses the HTML and adds the mail addresses to the kb.
        '''
        try:
            document_parser = dpCache.dpc.getDocumentParserFor( response )
        except w3afException:
            # Failed to find a suitable parser for the document
            pass
        else:
            # Search for email addresses
            for mail in document_parser.getEmails( self._domain_root ):
                if mail not in self._accounts:
                    self._accounts.append( mail )
                    
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName(mail)
                    i.setURL( response.getURI() )
                    msg = 'The mail account: "'+ mail + '" was found in: "'
                    msg += response.getURI() + '"'
                    i.setDesc( msg )
                    i['mail'] = mail
                    i['user'] = mail.split('@')[0]
                    i['url_list'] = [response.getURI(), ]
                    kb.kb.append( 'mails', 'mails', i )
                    kb.kb.append( self, 'mails', i )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d2 = 'Fetch the first "resultLimit" results from the Google search'
        o2 = option('resultLimit', self._result_limit, d2, 'integer')
        
        d3 = 'Do a fast search, when this feature is enabled, not all mail addresses are found'
        h3 = 'This method is faster, because it only searches for emails in the small page '
        h3 += 'snippet that google shows to the user after performing a common search.'
        o3 = option('fastSearch', self._fast_search, d3, 'boolean', help=h3)
        
        ol = optionList()
        ol.add(o2)
        ol.add(o3)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._result_limit = optionsMap['resultLimit'].getValue()
        self._fast_search = optionsMap['fastSearch'].getValue()
            
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
        This plugin finds mail addresses in google.
        
        Two configurable parameters exist:
            - resultLimit
            - fastSearch
        
        If fastSearch is set to False, this plugin searches google for : "@domain.com", requests all
        search results and parses them in order   to find new mail addresses. If the fastSearch 
        configuration parameter is set to True, only mail addresses that appear on the google 
        result page are parsed and added to the list, the result links are\'nt visited.
        '''
