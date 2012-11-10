'''
server_status.py

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

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.data.parsers.url import URL
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.exceptions import w3afRunOnce
from core.controllers.misc.decorators import runonce


class server_status(InfrastructurePlugin):
    '''
    Find new URLs from the Apache server-status cgi.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        InfrastructurePlugin.__init__(self)
        
        # Internal variables
        self._shared_hosting_hosts = []

    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzable_request ):
        '''
        Get the server-status and parse it.
        
        @param fuzzable_request: A fuzzable_request instance that contains
                                     (among other things) the URL to test.
        '''
        base_url = fuzzable_request.getURL().baseUrl()
        server_status_url = base_url.urlJoin( 'server-status' )
        response = self._uri_opener.GET( server_status_url, cache=True )
        
        if not is_404( response ) and response.getCode() not in range(400, 404):

            if 'apache' in response.getBody().lower():
                msg = 'Apache server-status module is enabled and accessible.'
                msg += ' The URL is: "%s"' % response.getURL()
                om.out.information( msg )
                
                self._extract_server_version( fuzzable_request, response )
                
                return self._extract_urls( fuzzable_request, response )
    
    def _extract_server_version(self, fuzzable_request, response):
        '''
        Get the server version from the HTML:
            <dl><dt>Server Version: Apache/2.2.9 (Unix)</dt>
        '''
        for version in re.findall('<dl><dt>Server Version: (.*?)</dt>', 
                                  response.getBody()):
            # Save the results in the KB so the user can look at it
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.setURL( response.getURL() )
            i.set_id( response.id )
            i.set_name( 'Apache Server version' )
            msg = 'The web server has the apache server status module enabled, '
            msg += 'which discloses the following remote server version: "%s".'
            i.set_desc( msg % version )

            om.out.information(i.get_desc())
            kb.kb.append( self, 'server', i )
    
    def _extract_urls(self, fuzzable_request, response):
        '''
        Extract information from the server-status page and return fuzzable
        requests to the caller.
        '''
        res = self._create_fuzzable_requests( response )

        # Now really parse the file and create custom made fuzzable requests
        regex = '<td>.*?<td nowrap>(.*?)</td><td nowrap>.*? (.*?) HTTP/1'
        for domain, path in re.findall(regex, response.getBody() ):
            
            if 'unavailable' in domain:
                domain = response.getURL().getDomain()
            
            # Check if the requested domain and the found one are equal.    
            if domain == response.getURL().getDomain():
                found_url = response.getURL().getProtocol() + '://' + domain + path
                found_url = URL(found_url)
            
                # They are equal, request the URL and create the fuzzable 
                # requests
                tmp_res = self._uri_opener.GET( found_url, cache=True )
                if not is_404( tmp_res ):
                    res.extend( self._create_fuzzable_requests( tmp_res ) )
            else:
                # This is a shared hosting server
                self._shared_hosting_hosts.append( domain )
        
        # Now that we are outsite the for loop, we can report the possible vulns
        if len( self._shared_hosting_hosts ):
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.setURL( fuzzable_request.getURL() )
            v.set_id( response.id )
            self._shared_hosting_hosts = list( set( self._shared_hosting_hosts ) )
            v['alsoInHosting'] = self._shared_hosting_hosts
            v.set_desc( 'The web application under test seems to be in a shared hosting.' )
            v.set_name( 'Shared hosting' )
            v.set_severity(severity.MEDIUM)
            
            kb.kb.append( self, 'shared_hosting', v )
            om.out.vulnerability( v.get_desc(), severity=v.get_severity() )
        
            msg = 'This list of domains, and the domain of the web application under test,'
            msg += ' all point to the same server:'
            om.out.vulnerability(msg, severity=severity.MEDIUM )
            for url in self._shared_hosting_hosts:
                om.out.vulnerability('- ' + url, severity=severity.MEDIUM )
                
        return res
        
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin fetches the server-status file used by Apache, and parses it.
        After parsing, new URLs are found, and in some cases, the plugin can deduce
        the existance of other domains hosted on the same server.
        '''
