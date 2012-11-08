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
import os
import xml.dom.minidom

import core.controllers.outputManager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afRunOnce
from core.controllers.misc.decorators import runonce
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList


class ria_enumerator(CrawlPlugin):
    '''
    Fingerprint Rich Internet Apps - Google Gears Manifest files, Silverlight and Flash.
    @author: Jon Rose ( jrose@owasp.org )
    '''
    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # User configured parameters
        self._wordlist = os.path.join('plugins' , 'crawl' , 'ria_enumerator',
                                      'common_filenames.db')
        
        # This is a list of common file extensions for google gears manifest:
        self._extensions = ['', '.php', '.json', '.txt', '.gears']
    
    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request ):
        '''
        Get the file and parse it.
        
        @param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        base_url = fuzzable_request.getURL().baseUrl()
        url_generator = self._url_generator( base_url, self._extensions, 
                                             self._wordlist )
        
        
        # Send the requests using threads:
        self._tm.threadpool.map(self._send_and_check, url_generator,
                                chunksize=10)
        
        return []
    
    def _url_generator(self, base_url, extensions, wordlist):
        '''
        Based on different files and user configurations, generate the URLs that
        need to be tested.
        
        @return: URLs
        '''
        ### Google Gears
        for ext in extensions:
            for word in file(wordlist):

                manifest_url = base_url.urlJoin( word.strip() + ext )
                yield manifest_url
                        
        ### CrossDomain.XML
        cross_domain_url = base_url.urlJoin( 'crossdomain.xml' )
        yield cross_domain_url
        
        ### CrossAccessPolicy.XML
        client_access_url = base_url.urlJoin( 'clientaccesspolicy.xml' )
        yield client_access_url
    
    def _send_and_check(self, url ):
        '''
        Analyze XML files.
        '''
        response = self._uri_opener.GET( url, cache=True )
        if is_404(response):
            return
        
        file_name = url.getFileName()
        
        om.out.debug( 'Checking response for %s in ria_enumerator.' % response)

        self._analyze_gears_manifest(url, response, file_name)
        self._analyze_crossdomain_clientaccesspolicy(url, response, file_name)

    def _analyze_gears_manifest(self, url, response, file_name):
        if '"entries":' in response:
            # Save it to the kb!
            i = info.info()
            i.setPluginName(self.get_name())
            i.set_name('Gears Manifest')
            i.setURL( url )
            i.set_id( response.id )
            desc = 'A gears manifest file was found at: "'+ url 
            desc += '".  Each file should be manually reviewed for sensitive'
            desc += ' information that may get cached on the client.' 
            i.set_desc( desc )
            kb.kb.append( self, url, i )
            om.out.information( i.get_desc() )
    
    def _analyze_crossdomain_clientaccesspolicy(self, url, response, file_name):
        try:
            dom = xml.dom.minidom.parseString( response.getBody() )
        except Exception:
            # Report this, it may be interesting for the final user
            # not a vulnerability per-se... but... it's information after all
            if 'allow-access-from' in response.getBody() or \
            'cross-domain-policy' in response.getBody() or \
            'cross-domain-access' in response.getBody():
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('Invalid ' + file_name)
                i.setURL( response.getURL() )
                i.setMethod( 'GET' )
                msg = 'The "' + file_name + '" file at: "' + response.getURL()
                msg += '" is not a valid XML.'
                i.set_desc( msg )
                i.set_id( response.id )
                kb.kb.append( self, 'info', i )
                om.out.information( i.get_desc() )
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
                    v.setPluginName(self.get_name())
                    v.setURL( response.getURL() )
                    v.setMethod( 'GET' )
                    v.set_name( 'Insecure "' + file_name + '" settings' )
                    v.set_severity(severity.LOW)
                    msg = 'The "' + file_name + '" file at "' + response.getURL() + '" allows'
                    msg += ' flash/silverlight access from any site.'
                    v.set_desc( msg )
                    v.set_id( response.id )
                    kb.kb.append( self, 'vuln', v )
                    om.out.vulnerability( v.get_desc(), severity=v.get_severity() )
                else:
                    i = info.info()
                    i.setPluginName(self.get_name())
                    i.set_name('Crossdomain allow ACL')
                    i.setURL( response.getURL() )
                    i.setMethod( 'GET' )
                    msg = 'The "' + file_name + '" file at "' + response.getURL() + '" allows'
                    msg += ' flash/silverlight access from "' + url + '".'
                    i.set_desc( msg )
                    i.set_id( response.id )
                    kb.kb.append( self, 'info', i )
                    om.out.information( i.get_desc() ) 	
                    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()    
        
        d = 'Wordlist to use in the manifest file name bruteforcing process.'
        o = opt_factory('wordlist', self._wordlist , d, 'string')
        ol.add(o)
        
        d = 'File extensions to use when brute forcing Gears Manifest files'
        o = opt_factory('manifestExtensions', self._extensions, d, 'list')
        ol.add(o)
        
        return ol
        
    def set_options( self, option_list ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @param OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        wordlist = option_list['wordlist'].get_value()
        if os.path.exists( wordlist ):
            self._wordlist = wordlist
        
        self._extensions = option_list['manifestExtensions'].get_value()

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for various Rich Internet Application files.  It
        currently searches for:
        
        Google gears manifests
        	These files are used to determine which files are locally cached by 
        	google gears. They do not get cleared when the browser cache is cleared 
        	and may contain sensitive information.
        									 
        Flex crossdomain.xml
        	This file stores domains which are allowed to make cross domain requests
        	to the server.
        
        Silverlight clientaccesspolicy.xml
        	This file determines which clients can access the server in place 
        	of the crossdomain.xml.
        	
        Two configurable parameters exists:
            - wordlist: The wordlist to be used in the gears bruteforce process.
            - manifestExtensions: File extensions to use during manifest bruteforcing.
        
        '''
