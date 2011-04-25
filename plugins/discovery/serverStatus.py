'''
serverStatus.py

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

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity
from core.data.parsers.urlParser import url_object

from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.controllers.w3afException import w3afRunOnce

import re


class serverStatus(baseDiscoveryPlugin):
    '''
    Find new URLs from the Apache server-status cgi.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._exec = True
        self._shared_hosting_hosts = []

    def discover(self, fuzzableRequest ):
        '''
        Get the server-status and parse it.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        res = []
        if not self._exec :
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:
            # Only run once
            self._exec = False
            
            base_url = fuzzableRequest.getURL().baseUrl()
            server_status_url = base_url.urlJoin( 'server-status' )
            response = self._urlOpener.GET( server_status_url, useCache=True )
            
            if not is_404( response ) and response.getCode() not in range(400, 404):
                msg = 'Apache server-status cgi exists. The URL is: "' + response.getURL() + '".'
                om.out.information( msg )
                
                # Create some simple fuzzable requests
                res.extend( self._createFuzzableRequests( response ) )

                # Get the server version
                # <dl><dt>Server Version: Apache/2.2.9 (Unix)</dt>
                for version in re.findall('<dl><dt>Server Version: (.*?)</dt>', response.getBody()):
                    # Save the results in the KB so the user can look at it
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.setName( 'Apache Server version' )
                    msg = 'The web server has the apache server status module enabled, '
                    msg += 'which discloses the following remote server version: "' + version + '".'
                    i.setDesc( msg )

                    om.out.information(i.getDesc())
                    kb.kb.append( self, 'server', i )
                
                # Now really parse the file and create custom made fuzzable requests
                regex = '<td>.*?<td nowrap>(.*?)</td><td nowrap>.*? (.*?) HTTP/1'
                for domain, path in re.findall(regex, response.getBody() ):
                    
                    if 'unavailable' in domain:
                        domain = response.getURL().getDomain()
                    
                    # Check if the requested domain and the found one are equal.    
                    if domain == response.getURL().getDomain():
                        found_url = response.getURL().getProtocol() + '://' + domain + path
                        found_url = url_object(found_url)
                    
                        # They are equal, request the URL and create the fuzzable requests
                        tmp_res = self._urlOpener.GET( found_url, useCache=True )
                        if not is_404( tmp_res ):
                            res.extend( self._createFuzzableRequests( tmp_res ) )
                    else:
                        # This is a shared hosting server
                        self._shared_hosting_hosts.append( domain )
                
                # Now that we are outsite the for loop, we can report the possible vulns
                if len( self._shared_hosting_hosts ):
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setURL( fuzzableRequest.getURL() )
                    v.setId( response.id )
                    self._shared_hosting_hosts = list( set( self._shared_hosting_hosts ) )
                    v['alsoInHosting'] = self._shared_hosting_hosts
                    v.setDesc( 'The web application under test seems to be in a shared hosting.' )
                    v.setName( 'Shared hosting' )
                    v.setSeverity(severity.MEDIUM)
                    
                    kb.kb.append( self, 'sharedHosting', v )
                    om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                
                    msg = 'This list of domains, and the domain of the web application under test,'
                    msg += ' all point to the same server:'
                    om.out.vulnerability(msg, severity=severity.MEDIUM )
                    for url in self._shared_hosting_hosts:
                        om.out.vulnerability('- ' + url, severity=severity.MEDIUM )
                
                # Check if well parsed
                elif 'apache' in response.getBody().lower():
                    msg = 'Couldn\'t find any URLs in the apache server status page. Two things can'
                    msg += ' trigger this:\n    - The Apache web server sent a server-status page'
                    msg += ' that the serverStatus plugin failed to parse or,\n    - The remote '
                    msg += ' web server has no traffic. If you are sure about the first one, please'
                    msg += ' report a bug.'
                    om.out.information( msg )
                    om.out.debug('The server-status body is: "'+response.getBody()+'"')
        
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
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
        This plugin fetches the server-status file used by Apache, and parses it. After parsing, new
        URLs are found, and in some cases, the plugin can deduce the existance of other domains
        hosted on the same server.
        '''
