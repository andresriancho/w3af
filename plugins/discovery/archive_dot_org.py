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
from core.data.parsers.dpCache import dpc as dpc
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
    INTERESTING_URLS_RE = 'http://web\.archive\.org/web/.*/http[s]?://%s/.*' 
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._already_visited = scalable_bloomfilter()
        
        # User configured parameters
        self._max_depth = 3

    def discover(self, fuzzableRequest ):
        '''
        Does a search in archive.org and searches for links on the html. Then
        searches those URLs in the target site. This is a time machine ! 
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                    (among other things) the URL to test.
        '''
        # Get the domain and set some parameters
        domain = fuzzableRequest.getURL().getDomain()
        if is_private_site( domain ):
            msg = 'There is no point in searching archive.org for "'+ domain + '"'
            msg += ' because it is a private site that will never be indexed.'
            om.out.information(msg)
            raise w3afRunOnce(msg)

        # Work
        start_url = self.ARCHIVE_START_URL % fuzzableRequest.getURL()
        start_url = url_object( start_url )
        references = self._spider_archive( [ start_url, ] , self._max_depth, domain )
        
        return self._analyze_urls( references )
            
    def _analyze_urls(self, references):
        '''
        Analyze which references are cached by archive.org
        
        @return: A list of query string objects for the URLs that are in
                 the cache AND are in the target web site.
        '''
        res = []
        real_URLs = []
        
        # Translate archive.org URL's to normal URL's
        for url in references:
            try:
                url = url.url_string[url.url_string.url.index('http', 1):]
            except Exception:
                pass
            else:
                real_URLs.append( url_object(url) )
        real_URLs = list(set(real_URLs))
        
        if len( real_URLs ):
            om.out.debug('Archive.org cached the following pages:')
            for u in real_URLs:
                om.out.debug('- %s' % u )
        else:
            om.out.debug('Archive.org did not find any pages.')
        
        # Verify if they exist in the target site and add them to
        # the result if they do.
        for real_url in real_URLs:
            if self._exists_in_target(real_url):
                qsr = HTTPQSRequest(real_url)
                res.append(qsr)
        
        if not res:
            om.out.debug('All pages found in archive.org cache are '
                         'missing in the target site.')
        else:
            om.out.debug('The following pages are in Archive.org cache '
                         'and also in the target site:')
            for req in res:
                om.out.debug('- %s' % req.getURI())

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
            if url in self._already_visited:
                continue
            
            self._already_visited.add( url )
                
            try:
                http_response = self._uri_opener.GET( url, cache=True )
                document_parser = dpc.getDocumentParserFor( http_response )
            except:
                continue

            # Note:
            # - With parsed_references I'm 100% that it's really something in 
            #   the HTML that the developer intended to add.
            #
            # - The re_references are the result of regular expressions, which
            #   in some cases are just false positives.
            parsed_references, _ = document_parser.getReferences()
            
            # Filter the ones we need
            url_regex_str = self.INTERESTING_URLS_RE % domain
            url_regex = re.compile(url_regex_str)
            new_urls = [ u for u in parsed_references if 
                         url_regex.match(u.url_string ) ]
            
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
        
        return res
    
    def _exists_in_target( self, url ):
        '''
        Check if a resource still exists in the target web site.
        
        @parameter url: The resource.
        '''
        try:
            response = self._uri_opener.GET( url, cache=True )
        except:
            return False
        else:
            if not is_404( response ):
                msg = 'The URL: "' + url + '" was found at archive.org and is'
                msg += ' STILL AVAILABLE in the target site.'
                om.out.debug( msg )
                return True
            else:
                msg = 'The URL: "' + url + '" was found at archive.org and was'
                msg += ' DELETED from the target site.'
                om.out.debug( msg )
                return False
            
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
