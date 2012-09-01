'''
robots_txt.py

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

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afRunOnce, w3afException
from core.controllers.misc.decorators import runonce
from core.controllers.core_helpers.fingerprint_404 import is_404

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info


class robots_txt(CrawlPlugin):
    '''
    Analyze the robots.txt file and find new URLs
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)
        
    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request ):
        '''
        Get the robots.txt file and parse it.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                                      (among other things) the URL to test.
        '''
        dirs = []
        
        base_url = fuzzable_request.getURL().baseUrl()
        robots_url = base_url.urlJoin( 'robots.txt' )
        http_response = self._uri_opener.GET( robots_url, cache=True )
        
        if not is_404( http_response ):
            # Save it to the kb!
            i = info.info()
            i.setPluginName(self.getName())
            i.setName('robots.txt file')
            i.setURL( robots_url )
            i.set_id( http_response.id )
            i.setDesc( 'A robots.txt file was found at: "'+ robots_url +'".' )
            kb.kb.append( self, 'robots.txt', i )
            om.out.information( i.getDesc() )


            # Work with it...
            dirs.append( robots_url )
            for line in http_response.getBody().split('\n'):
                
                line = line.strip()
                
                if len(line) > 0 and line[0] != '#' and \
                (line.upper().find('ALLOW') == 0 or \
                 line.upper().find('DISALLOW') == 0 ):
                    
                    url = line[ line.find(':') + 1 : ]
                    url = url.strip()
                    try:
                        url = base_url.urlJoin( url )
                    except:
                        # Simply ignore the invalid URL
                        pass
                    else:
                        dirs.append( url )

        self._tm.threadpool.map(self._get_and_parse, dirs)
    
    def _get_and_parse(self, url):
        '''
        GET and URL that was found in the robots.txt file, and parse it.
        
        @parameter url: The URL to GET.
        @return: None, everything is saved to self.out_queue.
        '''
        try:
            http_response = self._uri_opener.GET( url, cache=True )
        except KeyboardInterrupt, k:
            raise k
        except w3afException, w3:
            msg = 'w3afException while fetching page in crawl.robots_txt, error: "'
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
        This plugin searches for the robots.txt file, and parses it.
        
        This file is used to as an ACL that defines what URL's a search engine
        can access. By parsing this file, you can get more information about the
        target web application.
        '''
