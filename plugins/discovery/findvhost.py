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
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import *
import core.data.parsers.dpCache as dpCache
import socket
import difflib
from core.data.fuzzer.fuzzer import createRandAlNum
import core.data.constants.severity as severity

class findvhost(baseDiscoveryPlugin):
    '''
    Modify the HTTP Host header and try to find virtual hosts.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._firstExec = True
        
    def discover(self, fuzzableRequest ):
        '''
        Find virtual hosts.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        vHostList = []
        if self._firstExec :
            # Only run once
            self._firstExec = False
            vHostList = self._genericVhosts( fuzzableRequest )
        
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
        check for dead links and try them.
        '''
        res = []
        
        # Get some responses to compare later
        baseURL = urlParser.baseUrl( fuzzableRequest.getURL() )
        originalResponse = self._urlOpener.GET( fuzzableRequest.getURI() , useCache=True )
        baseResponse = self._urlOpener.GET( baseURL , useCache=True )
        
        dp = dpCache.dpc.getDocumentParserFor( originalResponse.getBody(), 'http://'+baseURL+'/' )
        
        # Set the non existant response
        nonExistant = 'iDoNotExistPleaseGoAwayNowOrDie' + createRandAlNum(4)
        self._nonExistantResponse = self._urlOpener.GET( baseURL, useCache=False, headers={'Host': nonExistant } )

        
        for link in dp.getReferences():
            domain = urlParser.getDomain( link )
            try:
                socket.gethostbyname( domain )
            except:
                # only work if domain is not resolved
                try:
                    vhostResponse = self._urlOpener.GET( baseURL, useCache=False, headers={'Host': domain } )
                except w3afException, w:
                    pass
                else:
                    # If they are *really* different (not just different by some chars) 
                    if difflib.SequenceMatcher( None, vhostResponse.getBody(), baseResponse.getBody() ).ratio() < 0.35 and \
                    difflib.SequenceMatcher( None, vhostResponse.getBody(), self._nonExistantResponse.getBody() ).ratio() < 0.35:
                        res.append( (domain, vhostResponse.id) )
                    else:
                        i = info.info()
                        i.setURL( fuzzableRequest.getURL() )
                        i.setMethod( 'GET' )
                        i.setDesc('Found a page that references a non existant domain: "' + link + '"' )
                        i.setId( vhostResponse.id )
                        kb.kb.append( self, 'findvhost', i )
                        om.out.information( i.getDesc() )
            else:
                pass
        
        return res 
        
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
                if difflib.SequenceMatcher( None, vhostResponse.getBody(), originalResponse.getBody() ).ratio() < 0.35 and \
                difflib.SequenceMatcher( None, vhostResponse.getBody(), self._nonExistantResponse.getBody() ).ratio() < 0.35:
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
        This plugin uses the HTTP Host header to find new virtual hosts. For example, if the intranet page is hosted
        in the same server that the public page, and the web server is misconfigured, this plugin will discover that
        virtual host.
        
        Please note that this plugin doesn't use any DNS technique to find this virtual hosts.
        '''
