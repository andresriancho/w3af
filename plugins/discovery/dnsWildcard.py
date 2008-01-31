'''
dnsWildcard.py

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
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import *
import re
import socket

class dnsWildcard(baseDiscoveryPlugin):
    '''
    Find out if www.site.com and site.com return the same page.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._exec = True

    def discover(self, fuzzableRequest ):
        '''
        Get www.site.com and site.com and compare responses.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec :
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:
            # Only run once
            self._exec = False
            
            if not re.match('\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?', urlParser.getDomain( fuzzableRequest.getURL() ) ):
                # Only do all this if this is a domain name!
                originalResponse = self._urlOpener.GET( urlParser.baseUrl( fuzzableRequest.getURL() ), useCache=True )
                
                domain = urlParser.getDomain( fuzzableRequest.getURL() )
                if domain.startswith('www.'):
                    dnsWildcardUrl = urlParser.getProtocol( fuzzableRequest.getURL() ) + '://' + domain.replace('www.', '') + '/'
                else:
                    dnsWildcardUrl = urlParser.getProtocol( fuzzableRequest.getURL() ) + '://www.' + domain + '/'
                
                self._testDNS( originalResponse, dnsWildcardUrl )
                self._testIP( originalResponse, domain )
                
                return []
    
    def _testIP( self, originalResponse, domain ):
        '''
        Check if http://ip(domain)/ == http://domain/
        '''
        ipAddress = socket.gethostbyname( domain )
        ipURL = urlParser.getProtocol( originalResponse.getURL() ) + '://'+ ipAddress + '/'
        try:
            modifiedResponse = self._urlOpener.GET( ipURL, useCache=True )
        except w3afException, w3:
            om.out.debug('An error ocurred while fetching IP address URL in dnsWildcard plugin.')
        else:
            if modifiedResponse.getBody() != originalResponse.getBody():
                i = info.info()
                i.setURL( modifiedResponse.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('The contents of ' + modifiedResponse.getURI() + ' differ from the contents of ' + originalResponse.getURI() )
                i.setId( modifiedResponse.id )
                kb.kb.append( self, 'dnsWildcard', i )
                om.out.information( i.getDesc() )
        
    def _testDNS( self, originalResponse, dnsWildcardUrl ):
        '''
        Check if http://www.domain/ == http://domain/
        '''
        try:
            modifiedResponse = self._urlOpener.GET( dnsWildcardUrl, useCache=True )
        except w3afException, w3:
            if 'Failed to resolve' in str(w3):
                i = info.info()
                i.setURL( originalResponse.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('The target site has no DNS wildcard.')
                kb.kb.append( self, 'dnsWildcard', i )
                om.out.information( i.getDesc() )
        else:
            if modifiedResponse.getBody() != originalResponse.getBody():
                i = info.info()
                i.setURL( modifiedResponse.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('The target site has no DNS wildcard, and the contents of ' + modifiedResponse.getURI() + ' differ from the contents of ' + originalResponse.getURI() )
                i.setId( modifiedResponse.id )
                kb.kb.append( self, 'dnsWildcard', i )
                om.out.information( i.getDesc() )
            else:
                i = info.info()
                i.setURL( originalResponse.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('The target site *has* a DNS wildcard configuration.' )
                i.setId( modifiedResponse.id )
                kb.kb.append( self, 'dnsWildcard', i )
                om.out.information( i.getDesc() )
                
                
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

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
        This plugin compares the contents of www.site.com and site.com and tries to verify if the target site
        has a DNS wildcard configuration or not.
        '''
