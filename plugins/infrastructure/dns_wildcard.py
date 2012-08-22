'''
dns_wildcard.py

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
import re
import socket

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.controllers.w3afException import w3afException, w3afRunOnce
from core.controllers.misc.decorators import runonce


class dns_wildcard(InfrastructurePlugin):
    '''
    Find out if www.site.com and site.com return the same page.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        InfrastructurePlugin.__init__(self)

    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzable_request ):
        '''
        Get www.site.com and site.com and compare responses.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        if not re.match('\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?',
                                fuzzable_request.getURL().getDomain() ):
            # Only do all this if this is a domain name!
            base_url = fuzzable_request.getURL().baseUrl()
            original_response = self._uri_opener.GET( base_url, cache=True )
            
            domain = fuzzable_request.getURL().getDomain()
            dns_wildcard_url = fuzzable_request.getURL().copy()
            
            #    TODO: This is weak! What if the subdomain is "www2"?
            #    Example: Target set by user is www2.host.tld.
            if domain.startswith('www.'):                    
                dns_wildcard_url.setDomain( domain.replace('www.', '') )
            else:
                dns_wildcard_url.setDomain( 'www.' + domain )
            
            self._test_DNS( original_response, dns_wildcard_url )
            self._test_IP( original_response, domain )
                
    def _test_IP( self, original_response, domain ):
        '''
        Check if http://ip(domain)/ == http://domain/
        '''
        try:
            ip_address = socket.gethostbyname( domain )
        except:
            return

        url = original_response.getURL()
        ip_url = url.copy()
        ip_url.setDomain( ip_address )

        try:
            modified_response = self._uri_opener.GET( ip_url, cache=True )
        except w3afException:
            om.out.debug('An error occurred while fetching IP address URL in dns_wildcard plugin.')
        else:
            if modified_response.getBody() != original_response.getBody():
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('Default domain')
                i.setURL( modified_response.getURL() )
                i.setMethod( 'GET' )
                msg = 'The contents of ' + modified_response.getURI()
                msg += ' differ from the contents of ' + original_response.getURI() 
                i.setDesc( msg )
                i.setId( modified_response.id )
                kb.kb.append( self, 'dns_wildcard', i )
                om.out.information( i.getDesc() )
        
    def _test_DNS( self, original_response, dns_wildcard_url ):
        '''
        Check if http://www.domain.tld/ == http://domain.tld/
        '''
        #
        #    I only want to perform an HTTP request if the domain
        #    actually exists. If not... we know it's going to fail
        #    and that will increase the library's error count, show
        #    a traceback, etc.
        #
        try:
            socket.gethostbyname( dns_wildcard_url.getDomain() )
        except:
            return
        
        try:
            modified_response = self._uri_opener.GET( dns_wildcard_url, cache=True )
        except w3afException, w3:
            if 'Failed to resolve' in str(w3):
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('No DNS wildcard')
                i.setURL( original_response.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('The target site has no DNS wildcard.')
                kb.kb.append( self, 'dns_wildcard', i )
                om.out.information( i.getDesc() )
        else:
            if modified_response.getBody() != original_response.getBody():
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('No DNS wildcard')
                i.setURL( modified_response.getURL() )
                i.setMethod( 'GET' )
                msg = 'The target site has no DNS wildcard, and the contents of '
                msg += modified_response.getURI() + ' differ from the contents of ' 
                msg += original_response.getURI()
                i.setDesc( msg )
                i.setId( modified_response.id )
                kb.kb.append( self, 'dns_wildcard', i )
                om.out.information( i.getDesc() )
            else:
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('DNS wildcard')
                i.setURL( original_response.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('The target site *has* a DNS wildcard configuration.' )
                i.setId( modified_response.id )
                kb.kb.append( self, 'dns_wildcard', i )
                om.out.information( i.getDesc() )
                
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin compares the contents of www.site.com and site.com and tries
        to verify if the target site has a DNS wildcard configuration or not.
        '''
