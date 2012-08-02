'''
archive_dot_org.py

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

import core.controllers.outputManager as om

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.misc.is_private_site import is_private_site
from core.controllers.w3afException import w3afRunOnce

from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.request.httpQsRequest import HTTPQSRequest
from core.data.parsers.urlParser import url_object
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.controllers.coreHelpers.fingerprint_404 import is_404


class archive_dot_org(baseDiscoveryPlugin):
    '''
    Search archive.org to find new pages in the target site.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    @author: Darren Bilby, thanks for the good idea!
    '''
    
    ARCHIVE_START_URL = 'http://web.archive.org/web/*/%s'
    INTERESTING_URLS_RE = '<a href="(http://web\.archive\.org/web/\d*?/https?://%s/.*?)"' 
    NOT_IN_ARCHIVE = '<p>Wayback Machine doesn&apos;t have that page archived.</p>'
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._already_crawled = scalable_bloomfilter()
        self._already_verified = scalable_bloomfilter()
        self._fuzzable_requests = []
        
        # User configured parameters
        self._max_depth = 3

    def discover(self, fuzzableRequest ):
        '''
        Does a search in archive.org and searches for links on the html. Then
        searches those URLs in the target site. This is a time machine ! 
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                    (among other things) the URL to test.
        '''
        self._fuzzable_requests = []
        domain = fuzzableRequest.getURL().getDomain()
        
        if is_private_site( domain ):
            msg = 'There is no point in searching archive.org for "%s"'
            msg += ' because it is a private site that will never be indexed.'
            om.out.information(msg % domain)
            raise w3afRunOnce(msg)

        # Initial check to verify if domain in archive
        start_url = self.ARCHIVE_START_URL % fuzzableRequest.getURL()
        start_url = url_object( start_url )
        http_response = self._uri_opener.GET( start_url, cache=True )
        
        if self.NOT_IN_ARCHIVE in http_response.body:
            msg = 'There is no point in searching archive.org for "%s"'
            msg += ' because they are not indexing this site.'
            om.out.information(msg % domain)
            raise w3afRunOnce(msg)
            
        references = self._spider_archive( [start_url,] , self._max_depth, domain )
        self._analyze_urls( references )
        
        return self._fuzzable_requests 
            
    def _analyze_urls(self, references):
        '''
        Analyze which references are cached by archive.org
        
        @return: A list of query string objects for the URLs that are in
                 the cache AND are in the target web site.
        '''
        real_URLs = []
        
        # Translate archive.org URL's to normal URL's
        for url in references:
            url = url.url_string[url.url_string.index('http', 1):]
            real_URLs.append( url_object(url) )
        real_URLs = list(set(real_URLs))
        
        if len( real_URLs ):
            om.out.debug('Archive.org cached the following pages:')
            for u in real_URLs:
                om.out.debug('- %s' % u )
        else:
            om.out.debug('Archive.org did not find any pages.')
        
        # Verify if they exist in the target site and add them to
        # the result if they do. Send the requests using threads:
        self._tm.threadpool.map(self._exists_in_target, real_URLs)            
        
        if not self._fuzzable_requests:
            om.out.debug('All pages found in archive.org cache are '
                         'missing in the target site.')
        else:
            om.out.debug('The following pages are in Archive.org cache '
                         'and also in the target site:')
            for req in self._fuzzable_requests:
                om.out.debug('- %s' % req.getURI())

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
            if url in self._already_crawled:
                continue
            
            self._already_crawled.add( url )
                
            try:
                http_response = self._uri_opener.GET( url, cache=True )
            except:
                continue

            # Filter the ones we need
            url_regex_str = self.INTERESTING_URLS_RE % domain
            matched_urls = re.findall(url_regex_str, http_response.body)
            new_urls = set([url_object(u).removeFragment() for u in matched_urls])
            
            # Go recursive
            if max_depth -1 > 0:
                if new_urls:
                    res.extend( new_urls )
                    res.extend( self._spider_archive( new_urls,
                                                      max_depth -1,
                                                      domain ) )
            else:
                msg = 'Some sections of the archive.org site were not analyzed'
                msg += ' because of the configured max_depth.'
                om.out.debug(msg)
                return new_urls
        
        return list(set(res))
    
    def _exists_in_target( self, url ):
        '''
        Check if a resource still exists in the target web site.
        
        @param url: The resource to verify.
        @return: None, the result is stored in self._fuzzable_requests
        '''
        if url in self._already_verified:
            return
        
        self._already_verified.add(url)
        
        response = self._uri_opener.GET( url, cache=True )

        if not is_404( response ):
            msg = 'The URL: "' + url + '" was found at archive.org and is'
            msg += ' STILL AVAILABLE in the target site.'
            om.out.debug( msg )
            self._fuzzable_requests.extend( self._createFuzzableRequests(response) )
        else:
            msg = 'The URL: "' + url + '" was found at archive.org and was'
            msg += ' DELETED from the target site.'
            om.out.debug( msg )
            
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        
        d = 'Maximum recursion depth for spidering process'
        h = 'The plugin will spider the archive.org site related to the target'
        h += ' site with the maximum depth specified in this parameter.'
        o = option('max_depth', self._max_depth, d, 'integer', help=h)
        ol.add(o)
        
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user 
        interface generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._max_depth = optionsMap['max_depth'].getValue()
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin does a search in archive.org and parses the results. It
        then uses the results to find new URLs in the target site. This plugin
        is a time machine !    
        '''
