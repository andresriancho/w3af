'''
ria_enumerator.py

Copyright 2009 Jon Rose

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
from core.controllers.w3afException import w3afRunOnce
from core.controllers.coreHelpers.fingerprint_404 import is_404

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity
import xml.dom.minidom
import os


class ria_enumerator(baseDiscoveryPlugin):
    '''
    Fingerprint Rich Internet Apps - Google Gears Manifest files, Silverlight and Flash.
    @author: Jon Rose ( jrose@owasp.org )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._exec = True
        
        # User configured parameters
        self._wordlist = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'ria_enumerator'
        self._wordlist += os.path.sep + 'common_filenames.db'
        
        # This is a list of common file extensions for google gears manifest:
        self._extensions = ['', '.php', '.json', '.txt', '.gears']
        
    def discover(self, fuzzableRequest ):
        '''
        Get the file and parse it.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                      (among other things) the URL to test.
        '''
        if not self._exec:
            raise w3afRunOnce()
        else:
            # Only run once
            self._exec = False

            base_url = fuzzableRequest.getURL().baseUrl()
            
            ### Google Gears
            for ext in self._extensions:
                for word in file(self._wordlist):

                    manifest_url = base_url.urlJoin( word.strip() + ext )

                    om.out.debug( 'Google Gears Manifest Testing "%s"' % (manifest_url)  )
                    http_response = self._urlOpener.GET( manifest_url, useCache=True )
                        
                    if '"entries":' in http_response and not is_404( http_response ):
                        # Save it to the kb!
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName('Gears Manifest')
                        i.setURL( manifest_url )
                        i.setId( http_response.id )
                        desc = 'A gears manifest file was found at: "'+ manifest_url 
                        desc += '".  Each file should be manually reviewed for sensitive'
                        desc += ' information that may get cached on the client.' 
                        i.setDesc( desc )
                        kb.kb.append( self, manifest_url, i )
                        om.out.information( i.getDesc() )
                            
            ### CrossDomain.XML
            cross_domain_url = base_url.urlJoin( 'crossdomain.xml' )
            om.out.debug( 'Checking crossdomain.xml file')
            response = self._urlOpener.GET( cross_domain_url, useCache=True )

            if not is_404( response ):
                self._checkResponse(response, 'crossdomain.xml')

            ### CrossAccessPolicy.XML
            client_access_url = base_url.urlJoin( 'clientaccesspolicy.xml' )
            om.out.debug( 'Checking clientaccesspolicy.xml file')
            response = self._urlOpener.GET( client_access_url, useCache=True )

            if not is_404( response ):
                self._checkResponse(response, 'clientaccesspolicy.xml')

        return []

    def _checkResponse(self, response, file_name ):
        '''
        Analyze XML files.
        '''
        om.out.debug( 'Checking XML response in ria_enumerator.')
        try:
            dom = xml.dom.minidom.parseString( response.getBody() )
        except Exception:
            # Report this, it may be interesting for the final user
            # not a vulnerability per-se... but... it's information after all
            if 'allow-access-from' in response.getBody() or \
            'cross-domain-policy' in response.getBody() or \
            'cross-domain-access' in response.getBody():
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('Invalid ' + file_name)
                i.setURL( response.getURL() )
                i.setMethod( 'GET' )
                msg = 'The "' + file_name + '" file at: "' + response.getURL()
                msg += '" is not a valid XML.'
                i.setDesc( msg )
                i.setId( response.id )
                kb.kb.append( self, 'info', i )
                om.out.information( i.getDesc() )
        else:
            if(file_name == 'crossdomain.xml'):
                url_list = dom.getElementsByTagName("allow-access-from")
                attribute = 'domain'
            if(file_name == 'clientaccesspolicy.xml'):
                url_list = dom.getElementsByTagName("domain")
                attribute = 'uri'

            for url in url_list:
                url = url.getAttribute(attribute)

                if url == '*':
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setURL( response.getURL() )
                    v.setMethod( 'GET' )
                    v.setName( 'Insecure "' + file_name + '" settings' )
                    v.setSeverity(severity.LOW)
                    msg = 'The "' + file_name + '" file at "' + response.getURL() + '" allows'
                    msg += ' flash/silverlight access from any site.'
                    v.setDesc( msg )
                    v.setId( response.id )
                    kb.kb.append( self, 'vuln', v )
                    om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                else:
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Crossdomain allow ACL')
                    i.setURL( response.getURL() )
                    i.setMethod( 'GET' )
                    i.setDesc( file_name + '" file allows access from: "' + url  + '".')
                    i.setId( response.id )
                    kb.kb.append( self, 'info', i )
                    om.out.information( i.getDesc() ) 	
                    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        d1 = 'Wordlist to use in the manifest file name bruteforcing process.'
        o1 = option('wordlist', self._wordlist , d1, 'string')
        
        d2 = 'File extensions to use when brute forcing Gears Manifest files'
        o2 = option('manifestExtensions', self._extensions, d2, 'list')

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol
        
    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        wordlist = OptionList['wordlist'].getValue()
        if os.path.exists( wordlist ):
            self._wordlist = wordlist
        
        self._extensions = OptionList['manifestExtensions'].getValue()

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
        This plugin searches for various Rich Internet Application files.  It currently searches for:
        
        Google gears manifests
        	These files are used to determine which files are locally cached by google gears.  
        	They do not get cleared when the browser cache is cleared and may contain sensitive information.
        									 
        Flex crossdomain.xml
        	This file stores domains which are allowed to make cross domain requests to the server.
        
        Silverlight clientaccesspolicy.xml
        	This file determines which clients can access the server in place of the crossdomain.xml.
        	
       Two configurable parameters exists:
            - wordlist: The wordlist to be used in the gears bruteforce process.
            - manifestExtensions: File extensions to use during manifest bruteforcing.
        
        '''
