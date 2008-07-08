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

from core.controllers.w3afException import w3afException
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
from core.data.searchEngines.googleSearchEngine import googleSearchEngine as google
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.urlParser as urlParser
import core.data.parsers.dpCache as dpCache
from core.controllers.w3afException import w3afRunOnce

class fingerGoogle(baseDiscoveryPlugin):
    '''
    Search Google using the Google API to get a list of users for a domain.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    '''
    Go here to get a API License : http://www.google.com/apis/
    
    Get pygoogle from : http://pygoogle.sourceforge.net/
    
    This plugin wont use proxy/proxy auth/auth/etc settings (for now). Original
    stand alone version that did not used pygoogle by Sergio Alvarez shadown@gmail.com .
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._run = True
        self._accounts = []
        
        # User configured 
        self._key = ''
        self._resultLimit = 300
        self._fastSearch = False
        
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
            
            self._google = google( self._urlOpener, self._key )
            self._domain = domain = urlParser.getDomain( fuzzableRequest.getURL() )
            self._domainRoot = urlParser.getRootDomain( domain )
            
            if self._fastSearch:
                self._doFastSearch( domain )
            else:
                self._doCompleteSearch( domain )
            
            self._tm.join( self )
            self.printUniq( kb.kb.getData( 'fingerGoogle', 'mails' ), None )
            return []

    def _doFastSearch( self, domain ):
        '''
        Only search for mail addresses in the google result page.
        '''
        try:
            resultPageObjects = self._google.getNResultPages( '@'+ self._domainRoot , self._resultLimit )
        except w3afException, w3:
            om.out.error(str(w3))
            # If I found an error, I don't want to be run again
            raise w3afRunOnce()
        else:
            # Happy happy joy, no error here!
            for result in resultPageObjects:
                self._parseDocument( result )
        
    def _doCompleteSearch( self, domain ):
        '''
        Performs a complete search for email addresses.
        '''
        try:
            resultPageObjects = self._google.getNResultPages( '@'+ self._domainRoot , self._resultLimit )
        except w3afException, w3:
            om.out.error(str(w3))
            # If I found an error, I don't want to be run again
            raise w3afRunOnce()
        else:
            # Happy happy joy, no error here!
            for result in resultPageObjects:
                targs = (result,)
                self._tm.startFunction( target=self._findAccounts, args=targs, ownerObj=self )
            
    def _findAccounts(self, googlePage ):
        '''
        Finds mails in google result page.
        
        @return: A list of valid accounts
        '''
        try:
            om.out.debug('Searching for mails in: ' + googlePage.getURL() )
            if self._domain == urlParser.getDomain( googlePage.getURL() ):
                response = self._urlOpener.GET( googlePage.getURL(), useCache=True, grepResult=True )
            else:
                response = self._urlOpener.GET( googlePage.getURL(), useCache=True, grepResult=False )
        except KeyboardInterrupt, e:
            raise e
        except w3afException, w3:
            om.out.debug('xUrllib exception raised while fetching page in fingerGoogle, error description: ' + str(w3) )
            self._newAccounts = []
        else:
            self._parseDocument( response )
            
    def _parseDocument( self, response ):
        '''
        Parses the HTML and adds the mail addresses to the kb.
        '''
        dp = dpCache.dpc.getDocumentParserFor( response.getBody(), 'http://'+self._domainRoot+'/' )
        for mail in dp.getEmails( self._domainRoot ):
            if mail not in self._accounts:
                self._accounts.append( mail )
                
                i = info.info()
                i.setName(mail)
                i.setURL( response.getURI() )
                i.setDesc( 'The mail account: "'+ mail + '" was found in: "' + response.getURI() + '"' )
                i['mail'] = mail
                i['user'] = mail.split('@')[0]
                kb.kb.append( 'mails', 'mails', i )
                kb.kb.append( self, 'mails', i )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Google API License key'
        h1 = 'To use this plugin you have to own your own google API license key OR you can directly use the search engine using clasic HTTP. If this parameter is left blank, the search engine will be used, otherwise the google webservice will be used.Go to http://www.google.com/apis/ to get more information.'
        o1 = option('key', self._key, d1, 'string', help=h1)
        
        d2 = 'Fetch the first "resultLimit" results from the Google search'
        o2 = option('resultLimit', self._resultLimit, d2, 'integer')
        
        d3 = 'Do a fast search, when this feature is enabled, not all mail addresses are found'
        h3 = 'This method is faster, because it only searches for emails in the small page snippet that google shows to the user after performing a common search.'
        o3 = option('fastSearch', self._fastSearch, d3, 'boolean', help=h3)
        
        ol = optionList()
        ol.add(o1)
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
        self._key = optionsMap['key'].getValue()
        self._resultLimit = optionsMap['resultLimit'].getValue()
        self._fastSearch = optionsMap['fastSearch'].getValue()
            
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
            - key
            - resultLimit
            - fastSearch
        
        If fastSearch is set to False, this plugin searches google for : "@domain.com", requests all search results and parses 
        them in order   to find new mail addresses. If the fastSearch configuration parameter is set to True, only mail addresses
        that appear on the google result page are parsed and added to the list, the result links are\'nt visited.
        '''
