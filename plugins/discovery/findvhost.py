'''
findvhost.py

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
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import *
import core.data.parsers.dpCache as dpCache
import socket
from core.controllers.misc.levenshtein import relative_distance
from core.data.fuzzer.fuzzer import createRandAlNum
import core.data.constants.severity as severity

class findvhost(baseDiscoveryPlugin):
    '''
    Modify the HTTP Host header and try to find virtual hosts.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._firstExec = True
        self._alreadyQueried = []
        self._canResolveDomainNames = False
        
    def discover(self, fuzzableRequest ):
        '''
        Find virtual hosts.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        vHostList = []
        if self._firstExec:
            # Only run once
            self._firstExec = False
            vHostList = self._genericVhosts( fuzzableRequest )
            
            # Set this for later
            self._canResolveDomainNames = self._canResolveDomains()
            
        
        # I also test for ""dead links"" that the web programmer left in the page
        # For example, If w3af finds a link to "http://corporative.intranet.corp/" it will try to
        # resolve the dns name, if it fails, it will try to request that page from the server
        vHostList.extend( self._deadLinks( fuzzableRequest ) )
        
        # Report our findings
        for vhost, id in vHostList:
            v = vuln.vuln()
            v.setURL( fuzzableRequest.getURL() )
            v.setMethod( 'GET' )
            v.setName( 'Shared hosting' )
            v.setSeverity(severity.LOW)
            v.setDesc('Found a new virtual host at the target web server, virtual host name is: "' + vhost + '"' )
            v.setId( id )
            kb.kb.append( self, 'findvhost', v )
            om.out.information( v.getDesc() )       
        
        return []
        
    def _deadLinks( self, fuzzableRequest ):
        '''
        Find every link on a HTML document verify if the domain is reachable or not; after that, verify if the web
        found a different name for the target site or if we found a new site that is linked. If the link points to a dead
        site then report it (it could be pointing to some private address or something...)
        '''
        res = []
        
        # Get some responses to compare later
        baseURL = urlParser.baseUrl( fuzzableRequest.getURL() )
        originalResponse = self._urlOpener.GET( fuzzableRequest.getURI() , useCache=True )
        baseResponse = self._urlOpener.GET( baseURL , useCache=True )
        
        try:
            dp = dpCache.dpc.getDocumentParserFor( originalResponse )
        except w3afException:
            # Failed to find a suitable parser for the document
            return []
        
        # Set the non existant response
        nonExistant = 'iDoNotExistPleaseGoAwayNowOrDie' + createRandAlNum(4) 
        self._nonExistantResponse = self._urlOpener.GET( baseURL, useCache=False, headers={'Host': nonExistant } )

        for link in dp.getReferences():
            domain = urlParser.getDomain( link )
            
            #
            # First section, find internal hosts using the HTTP Host header:
            #
            if domain not in self._alreadyQueried:
                # If the parsed page has an external link to www.google.com
                # then I'll send a request to the target site, with Host: www.google.com
                # This sucks, but it's cool if the document has a link to http://some.internal.site.target.com/
                try:
                    vhostResponse = self._urlOpener.GET( baseURL, useCache=False, headers={'Host': domain } )
                except w3afException, w:
                    pass
                else:
                    self._alreadyQueried.append( domain )
                    if relative_distance( vhostResponse.getBody(), baseResponse.getBody() ) < 0.35 and \
                    relative_distance( vhostResponse.getBody(), self._nonExistantResponse.getBody() ) < 0.35:
                        # If they are *really* different (not just different by some chars) I may have found
                        # something interesting!
                        res.append( (domain, vhostResponse.id) )

            #
            # Second section, find hosts using failed DNS resolutions
            #
            if self._canResolveDomainNames:
                try:
                    socket.gethostbyname( domain )
                except:
                    i = info.info()
                    i.setName('Internal hostname in HTML link')
                    i.setURL( fuzzableRequest.getURL() )
                    i.setMethod( 'GET' )
                    i.setId( originalResponse.id )
                    msg = 'The content of "'+ fuzzableRequest.getURL() +'" references a non '
                    msg += 'existant domain: "' + link + '"'
                    i.setDesc( msg )
                    kb.kb.append( self, 'findvhost', i )
                    om.out.information( i.getDesc() )
        
        return res 
    
    def _canResolveDomains(self):
        '''
        This method was added to verify if w3af can resolve domain names
        using the OS configuration (/etc/resolv.conf in linux) or if we are in some
        strange LAN where we can't.
        
        @return: True if we can resolve domain names.
        '''
        try:
            socket.gethostbyname( 'www.w3.org' )
        except:
            return False
        else:
            return True
    
    def _genericVhosts( self, fuzzableRequest ):
        '''
        Test some generic virtual hosts, only do this once.
        '''
        res = []
        baseURL = urlParser.baseUrl( fuzzableRequest.getURL() )
        
        commonVhostList = self._getCommonVirtualHosts( urlParser.getDomain( baseURL ) )
        
        # Get some responses to compare later
        originalResponse = self._urlOpener.GET( baseURL, useCache=True )
        nonExistant = 'iDoNotExistPleaseGoAwayNowOrDie' + createRandAlNum(4)
        self._nonExistantResponse = self._urlOpener.GET( baseURL, useCache=False, headers={'Host': nonExistant } )
        
        for commonVhost in commonVhostList:
            try:
                vhostResponse = self._urlOpener.GET( baseURL, useCache=False, headers={'Host': commonVhost } )
            except w3afException, w3:
                pass
            else:
                # If they are *really* different (not just different by some chars) 
                if relative_distance( vhostResponse.getBody(), originalResponse.getBody() ) < 0.35 and \
                relative_distance( vhostResponse.getBody(), self._nonExistantResponse.getBody() ) < 0.35:
                    res.append( (commonVhost, vhostResponse.id) )
        
        return res
    
    def _getCommonVirtualHosts( self, domain ):
        res = []
        
        for subdomain in ['intranet', 'intra', 'extranet', 'extra' , 'test' , 'old' , 'new' , 'admin' ]:
            # intranet
            res.append( subdomain )
            # intranet.www.targetsite.com
            res.append( subdomain + '.' + domain )
            # intranet.targetsite.com
            res.append( subdomain + '.' + urlParser.getRootDomain( domain ) )
            # This is for:
            # intranet.targetsite
            res.append( subdomain + '.' + urlParser.getRootDomain( domain ).split('.')[0] )
        
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
        This plugin uses the HTTP Host header to find new virtual hosts. For example, if the intranet page is hosted
        in the same server that the public page, and the web server is misconfigured, this plugin will discover that
        virtual host.
        
        Please note that this plugin doesn't use any DNS technique to find this virtual hosts.
        '''
