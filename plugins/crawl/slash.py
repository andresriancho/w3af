'''
slash.py

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
from functools import partial 

from core.controllers.basePlugin.baseCrawlPlugin import baseCrawlPlugin
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.misc.levenshtein import relative_distance_lt

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.parsers.urlParser import url_object


class slash(baseCrawlPlugin):
    '''
    Identify if the resource http://host.tld/spam/ and 
    http://host.tld/spam are the same.
    
    @author: Nicolas Rotta ( nicolas.rotta@gmail.com )  
    '''
    
    def __init__(self):
        baseCrawlPlugin.__init__(self)
        self._already_visited = scalable_bloomfilter()
        
    def crawl(self, fuzzable_request):
        '''
        Generates a new URL by adding or substracting the '/' character.      
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
            (among other things) the URL to test.
        '''     
        if fuzzable_request.getURL() not in self._already_visited:
            fr_slash = self._get_fuzzed_request(fuzzable_request)
            
            self._already_visited.add(fuzzable_request.getURL())
            self._already_visited.add(fr_slash.getURL())
            
            if fr_slash.getURL() != fuzzable_request.getURL():

                http_response_list = []
                add_http_response = partial(self._add_http_responses, http_response_list)
            
                self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                              [fuzzable_request,fr_slash],
                                              callback=add_http_response)
            
                return self._analyze(http_response_list)
                
        return []

    def _get_fuzzed_request(self, fuzzable_request):
        '''
        Generate a new Url by adding or substracting the '/' character.
        
        @param fuzzable_request: The original fuzzable_request
        @return: The modified fuzzable_request.
        '''
        fr = fuzzable_request.copy()
        
        url_string = str(fuzzable_request.getURL()) 
        
        if url_string.endswith('/'):
            new_url = url_object(url_string.rstrip('/'))
        else:
            new_url = url_object(url_string + '/')
        
        fr.setURL(new_url)
        return fr

    def _add_http_responses(self, response_list, fr, http_response):
        response_list.append(http_response)

    def _analyze(self, http_response_list):
        '''
        Analyze the HTTP responses which come inside and return new fuzzable
        requests (if any).
        '''
        if len(http_response_list) == 2:
            http_response_a = http_response_list[0]
            http_response_b = http_response_list[1]
            a_body = http_response_b.getBody()
            b_body = http_response_a.getBody()
            if relative_distance_lt(a_body, b_body, 0.7) \
            and not is_404(http_response_a) and not is_404(http_response_b):
                res = []
                res.extend(self._createfuzzable_requests(http_response_a))
                res.extend(self._createfuzzable_requests(http_response_b))
                return res
        
        return []
    
    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Identify if the resource http://host.tld/spam/ and http://host.tld/spam
        are the same.      
        '''
