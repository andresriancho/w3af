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
from core.controllers.misc.levenshtein import relative_distance_lt
from core.data.dc.headers import Headers


class dns_wildcard(InfrastructurePlugin):
    '''
    Find out if www.site.com and site.com return the same page.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    SIMPLE_IP_RE = re.compile('\d?\d?\d\.\d?\d?\d\.\d?\d?\d\.\d?\d?\d')

    def __init__(self):
        InfrastructurePlugin.__init__(self)
        
    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzable_request ):
        '''
        Get www.site.com and site.com and compare responses.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        
        # Only do all this if this is a domain name!
        if not self.SIMPLE_IP_RE.match(fuzzable_request.getURL().getDomain()):
            
            base_url = fuzzable_request.getURL().baseUrl()
            original_response = self._uri_opener.GET( base_url, cache=True )
            
            domain = fuzzable_request.getURL().getDomain()
            dns_wildcard_url = fuzzable_request.getURL().copy()
            
            root_domain = base_url.getRootDomain()
            if len(domain) > len(root_domain):
                # Remove the last subdomain and test with that
                domain_without_subdomain = '.'.join( domain.split('.')[1:] )
                dns_wildcard_url.setDomain( domain_without_subdomain )
            else:
                dns_wildcard_url.setDomain( 'foobar.' + domain )
            
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
        except w3afException, w3:
            msg = 'An error occurred while fetching IP address URL in ' \
                  ' dns_wildcard plugin: "%s"' % w3 
            om.out.debug( msg )
        else:
            if relative_distance_lt(modified_response.getBody(), 
                                    original_response.getBody(), 0.35):
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('Default domain')
                i.setURL( modified_response.getURL() )
                i.setMethod( 'GET' )
                msg = 'The contents of ' + modified_response.getURI()
                msg += ' differ from the contents of ' + original_response.getURI() 
                i.set_desc( msg )
                i.set_id( modified_response.id )
                kb.kb.append( self, 'dns_wildcard', i )
                om.out.information( i.get_desc() )
        
    def _test_DNS( self, original_response, dns_wildcard_url ):
        '''
        Check if http://www.domain.tld/ == http://domain.tld/
        '''
        headers = Headers([('Host', dns_wildcard_url.getDomain())])
        try:
            modified_response = self._uri_opener.GET( original_response.getURL(),
                                                      cache=True,
                                                      headers=headers)
        except w3afException:
            return
        else:
            if relative_distance_lt(modified_response.getBody(), 
                                    original_response.getBody(), 0.35):
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('No DNS wildcard')
                i.setURL( dns_wildcard_url )
                i.setMethod( 'GET' )
                msg = 'The target site has NO DNS wildcard, and the contents of ' \
                      '"%s" differ from the contents of "%s".' 
                i.set_desc( msg % (dns_wildcard_url, original_response.getURL()) )
                i.set_id( modified_response.id )
                kb.kb.append( self, 'dns_wildcard', i )
                om.out.information( i.get_desc() )
            else:
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('DNS wildcard')
                i.setURL( original_response.getURL() )
                i.setMethod( 'GET' )
                msg = 'The target site has a DNS wildcard configuration, the' \
                      ' contents of "%s" are equal to the ones of "%s".'
                i.set_desc( msg % (dns_wildcard_url, original_response.getURL()) )
                i.set_id( modified_response.id )
                kb.kb.append( self, 'dns_wildcard', i )
                om.out.information( i.get_desc() )
                
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin compares the contents of www.site.com and site.com and tries
        to verify if the target site has a DNS wildcard configuration or not.
        '''
