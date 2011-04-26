'''
archiveDotOrg.py

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

from core.controllers.misc.is_private_site import is_private_site
from core.data.request.httpQsRequest import httpQsRequest
from core.controllers.w3afException import w3afException
from core.data.parsers.dpCache import dpc as dpc
from core.data.parsers.urlParser import url_object
import core.data.kb.knowledgeBase as kb

from core.data.bloomfilter.pybloom import ScalableBloomFilter
from core.controllers.coreHelpers.fingerprint_404 import is_404

import re


class archiveDotOrg(baseDiscoveryPlugin):
    '''
    Search archive.org to find new pages in the target site.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    @author: Darren Bilby, thanks for the good idea!
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._already_visited = ScalableBloomFilter()
        
        # User configured parameters
        self._max_depth = 3

    def discover(self, fuzzableRequest ):
        '''
        Does a search in archive.org and searches for links on the html. Then searches those
        URLs in the target site. This is a time machine ! 
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things)
                                                      the URL to test.
        '''
        # Get the domain and set some parameters
        domain = fuzzableRequest.getURL().getDomain()
        if is_private_site( domain ):
            msg = 'There is no point in searching archive.org for "'+ domain + '"'
            msg += ' because it is a private site that will never be indexed.'
            raise w3afException(msg)
        else:
            # Work
            om.out.debug( 'archiveDotOrg plugin is testing: ' + fuzzableRequest.getURL() )
            
            start_url = 'http://web.archive.org/web/*/' + fuzzableRequest.getURL()
            start_url = url_object( start_url )
            references = self._spider_archive( [ start_url, ] , self._max_depth, domain )
            
            return self._analyze_urls( references )
            
    def _analyze_urls(self, references):
        '''
        Analyze what references are cached by archive.org
        
        @return: A list of query string objects for the URLs that are in the cache AND are in the
                    target web site.
        '''
        # Init some internal variables
        res = []
    
        # Translate archive.org URL's to normal URL's
        real_URLs = []
        for url in references:
            try:
                url = url.url_string[url.url_string.url.index('http', 1):]
            except Exception:
                pass
            else:
                real_URLs.append( url )
        real_URLs = list(set(real_URLs))
        
        if len( real_URLs ):
            om.out.debug('Archive.org cached the following pages:')
            for i in real_URLs:
                om.out.debug('- ' + i )
        else:
            om.out.debug('Archive.org did not find any pages.')
        
        # Verify if they exist in the target site and add them to the result if they do.
        for real_url in real_URLs:
            if self._exists_in_target( real_url ):
                QSObject = real_url.getQueryString()
                qsr = httpQsRequest()
                qsr.setURI( real_url )
                qsr.setDc( QSObject )
                res.append( qsr )

        if len( res ):
            msg = 'The following pages are in Archive.org cache and also in'
            msg += ' the target site:'
            om.out.debug(msg)
            for i in res:
                om.out.debug('- ' + i.getURI() )
        else:
            om.out.debug('All pages found in archive.org cache are missing in the target site.')
            
        return res
    
    def _spider_archive( self, url_list, max_depth, domain ):
        '''
        Perform a classic web spidering process.
        
        @parameter url_list: The list of URL strings
        @parameter max_depth: The max link depth that we have to follow.
        @parameter domain: The domain name we are checking
        '''
        # Start the recursive spidering         
        res = []
        
        for url in url_list:
            if url not in self._already_visited:
                self._already_visited.add( url )
                
                try:
                    http_response = self._urlOpener.GET( url, useCache=True )
                except Exception:
                    pass
                else:
                    # Get the references
                    try:
                        document_parser = dpc.getDocumentParserFor( http_response )
                    except w3afException:
                        # Failed to find a suitable document parser
                        pass
                    else:
                        # Note:
                        # - With parsed_references I'm 100% that it's really something in the HTML
                        # that the developer intended to add.
                        #
                        # - The re_references are the result of regular expressions, which in some cases
                        # are just false positives.
                        parsed_references, re_references = document_parser.getReferences()
                        
                        # Filter the ones I want
                        url_regex = 'http://web\.archive\.org/web/.*/http[s]?://' + domain + '/.*'
                        new_urls = [ u for u in parsed_references if re.match(url_regex, u.url_string ) ]
                        
                        # Go recursive
                        if max_depth -1 > 0:
                            if new_urls:
                                res.extend( new_urls )
                                res.extend( self._spider_archive( new_urls, max_depth -1, domain ) )
                        else:
                            msg = 'Some sections of the archive.org site were not analyzed because'
                            msg += ' of the configured max_depth.'
                            om.out.debug(msg)
                            return new_urls
        
        return res
    
    def _exists_in_target( self, url ):
        '''
        Check if a resource still exists in the target web site.
        
        @parameter url: The resource.
        '''
        res = False
        
        try:
            response = self._urlOpener.GET( url, useCache=True )
        except KeyboardInterrupt,e:
            raise e
        except w3afException,e:
            pass
        else:
            if not is_404( response ):
                res = True
        
        if res:
            msg = 'The URL: "' + url + '" was found at archive.org and is STILL'
            msg += ' AVAILABLE in the target site.'
            om.out.debug( msg )
        else:
            msg = 'The URL: "' + url + '" was found at archive.org and was DELETED'
            msg += ' from the target site.'
            om.out.debug( msg )
        
        return res
            
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Maximum recursion depth for spidering process'
        h1 = 'The plugin will spider the archive.org site related to the target site with the'
        h1 += 'maximum depth specified in this parameter.'
        o1 = option('max_depth', self._max_depth, d1, 'integer', help=h1)

        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._max_depth = optionsMap['max_depth'].getValue()
        
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
        This plugin does a search in archive.org and parses the results. It then uses the results to find new
        URLs in the target site. This plugin is a time machine !    
        '''
