'''
fingerMSN.py

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

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.searchEngines.msn import msn as msn
import core.data.parsers.urlParser as urlParser
import core.data.parsers.dpCache as dpCache


class fingerMSN(baseDiscoveryPlugin):
    '''
    Search MSN to get a list of users for a domain.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._run = True
        self._accounts = []
        
        # User configured 
        self._result_limit = 300
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._run:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # This plugin will only run one time. 
            self._run = False
            
            msn_se = msn( self._urlOpener )
            
            self._domain = domain = urlParser.getDomain( fuzzableRequest.getURL() )
            self._domain_root = urlParser.getRootDomain( domain )
            
            results = msn_se.getNResults('@'+ self._domain_root, self._result_limit)
                
            for result in results:
                targs = (result,)
                self._tm.startFunction( target=self._find_accounts, args=targs , ownerObj=self )

            self._tm.join( self )
            self.printUniq( kb.kb.getData( 'fingerMSN', 'mails' ), None )
                
        return []
    
    def _find_accounts(self, msn_page ):
        '''
        Finds mails in msn result.
        
        @return: A list of valid accounts
        '''
        try:
            om.out.debug('Searching for mails in: ' + msn_page.URL )
            if self._domain == urlParser.getDomain( msn_page.URL ):
                response = self._urlOpener.GET( msn_page.URL, useCache=True, grepResult=True )
            else:
                response = self._urlOpener.GET( msn_page.URL, useCache=True, grepResult=False )
        except KeyboardInterrupt, e:
            raise e
        except w3afException, w3:
            msg = 'xUrllib exception raised while fetching page in fingerMSN,'
            msg += ' error description: ' + str(w3)
            om.out.debug( msg )
        else:
            
            # I have the response object!
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
                        i.setURL( msn_page.URL )
                        i.setName( mail )
                        msg = 'The mail account: "'+ mail + '" was found in: "' + msn_page.URL + '"'
                        i.setDesc( msg )
                        i['mail'] = mail
                        i['user'] = mail.split('@')[0]
                        kb.kb.append( 'mails', 'mails', i )
                        kb.kb.append( 'fingerMSN', 'mails', i )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Fetch the first "resultLimit" results from the MSN search'
        o1 = option('resultLimit', self._result_limit, d1, 'integer')
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._result_limit = optionsMap['resultLimit'].getValue()
            
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
        This plugin finds mail addresses in MSN search engine.
        
        One configurable parameter exist:
            - resultLimit
        
        This plugin searches MSN for : "@domain.com", requests all search results and parses them in order
        to find new mail addresses.
        '''
