'''
urllist_txt.py

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
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afRunOnce, w3afException
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.misc.decorators import runonce


class urllist_txt(CrawlPlugin):
    '''
    Analyze the urllist.txt file and find new URLs
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)
        
    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request ):
        '''
        Get the urllist.txt file and parse it.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        base_url = fuzzable_request.getURL().baseUrl()
        urllist_url = base_url.urlJoin( 'urllist.txt' )
        http_response = self._uri_opener.GET( urllist_url, cache=True )
        
        if not is_404( http_response ):
            if self._is_urllist_txt(base_url, http_response.getBody() ):
                # Save it to the kb!
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('urllist.txt file')
                i.setURL( urllist_url )
                i.set_id( http_response.id )
                i.set_desc( 'A urllist.txt file was found at: "%s".' % urllist_url )
                kb.kb.append( self, 'urllist.txt', i )
                om.out.information( i.get_desc() )
            
            # Even in the case where it is NOT a valid urllist.txt it might be
            # the case where some URLs are present, so I'm going to extract them
            # from the file as if it is a valid urllist.txt
            
            url_generator = self._extract_urls_generator( base_url, 
                                                          http_response.getBody() )
            
            # Send the requests using threads:
            self._tm.threadpool.map(self._get_and_parse, url_generator)

    def _is_urllist_txt(self, base_url, body):
        '''
        @return: True if the body is a urllist.txt
        '''
        is_urllist = 5
        for line in body.split('\n'):
            
            line = line.strip()
            
            if not line.startswith('#') and line:    
                try:
                    base_url.urlJoin( line )
                except:
                    is_urllist -= 1
        
        return bool(is_urllist)
    
    def _extract_urls_generator(self, base_url, body):
        '''
        @param body: The urllist.txt body
        @yield: a URL object from the urllist.txt body
        '''
        for line in body.split('\n'):
            
            line = line.strip()
            
            if not line.startswith('#') and line:    
                try:
                    url = base_url.urlJoin( line )
                except:
                    pass
                else:
                    yield url
    
    def _get_and_parse(self, url):
        '''
        GET and URL that was found in the robots.txt file, and parse it.
        
        @parameter url: The URL to GET.
        @return: None, everything is put() to self.output_queue.
        '''
        try:
            http_response = self._uri_opener.GET( url, cache=True )
        except w3afException, w3:
            msg = 'w3afException while fetching page in crawl.urllist_txt, error: "'
            msg += str(w3) + '"'
            om.out.debug( msg )
        else:
            if not is_404( http_response ):
                for fr in self._create_fuzzable_requests( http_response ):
                    self.output_queue.put(fr)
        
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for the urllist.txt file, and parses it. The 
        urllist.txt file is/was used by Yahoo's search engine.
        '''
