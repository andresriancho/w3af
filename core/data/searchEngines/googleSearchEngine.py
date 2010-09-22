'''
googleSearchEngine.py

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
import urllib

import sys

try:
    import extlib.simplejson as json
except:
    import simplejson as json

import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.data.searchEngines.searchEngine import searchEngine as searchEngine
import core.data.parsers.urlParser as urlParser


GOOGLE_AJAX_SEARCH_URL = "http://ajax.googleapis.com/ajax/services/search/web?"
GOOGLE_AJAX_MAX_RES_PER_PAGE = 8
GOOGLE_AJAX_MAX_START_INDEX = 56
GOOGLE_SEARCH_URL = "http://www.google.com/search?"
GOOGLE_SET_SEARCH_URL = "http://labs.google.com/sets?hl=en"





class googleSearchEngine(searchEngine):
    '''
    This class is a wrapper for doing google searches. It allows the user to use pygoogle or simply do GET requests
    to google.com .
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, urlOpener):
        searchEngine.__init__(self)
        self._urlOpener = urlOpener
        
    def search(self, query, start, count=10):
        '''
        Perform a google search and return the resulting URLs.
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''
        # First try using Google's AJAX API. Right now it only will fetch
        # 64 results top
        res = self.do_ajax_search(query, start, count)[0]        
        res_qty = len(res)
        # If we got less than expected, call traditional search
        if res_qty < count:
            start += res_qty
            count -= res_qty
            res += self.met_search(query, start, count)[0]
            
        om.out.debug("Google search for: '%s' returned %s results." % \
                        (query, len(res)))
        return res
    
    def pagesearch(self, query, start, count=10):
        '''
        Perform a google search and return the google result pages.
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''        
        _, res_pages = self.met_search( query, start, count )
        return res_pages
    
    def set( self, inputStringList ):
        '''
        Performs a google set search.
        http://labs.google.com/sets
        '''
        results = []
        
        if len( inputStringList ) != 0:
            # I'll use the first 5 inputs
            inputStringList = list(inputStringList)[:5]
        
            # This is a search for a set with input blue and white
            #http://labs.google.com/sets?hl=en&q1=blue&q2=white&q3=&q4=
            #&q5=&btn=Small+Set+%2815+items+or+fewer%29
            url = GOOGLE_SET_SEARCH_URL
            qParameter = 1
            
            for inputString in inputStringList:
                url += '&q' + str( qParameter ) + '=' + urllib.quote_plus( inputString )
                qParameter += 1
            url += '&btn=Small+Set+%2815+items+or+fewer%29'
            
            # Now I get the results
            response = self._urlOpener.GET( url , headers=self._headers, useCache=True,
                                                            grepResult=False )
            
            regex = '<font face="Arial, sans-serif" size=-1>'
            regex += '<a href="http://www.google.com/search\?hl=en&amp;q=(.*?)">'
            for result_str in re.findall( regex, response.getBody() ):
                results.append( urllib.unquote_plus( result_str.lower() ) )
        
        results = [ x for x in results if x not in inputStringList ] 
        om.out.debug('Google set search returned:')
        for i in results:
            om.out.debug('- ' + i )
        return results
    
    
    def do_ajax_search(self, query, start=0, count=10):
        """
        Search the web using Google's AJAX API. Note that Google restricts
        this API to return only the first 64 results.
        
        @parameter query: query to perform
        @parameter start: start index.
        @parameter count: amount of results to fetch
        @return: 
        """
        result_list = []
        res_pages = []

        max_start = min(start + count,
                            GOOGLE_AJAX_MAX_START_INDEX + 
                            GOOGLE_AJAX_MAX_RES_PER_PAGE)

        while start < max_start:
            
            size = min(max_start - start, GOOGLE_AJAX_MAX_RES_PER_PAGE)
            
            # Build param dict; then encode it
            params_dict = {'v': '1.0', 'q': query,
                           'rsz': size, 'start': start}
            params = urllib.urlencode(params_dict)
            
            # Do the request
            try:
                resp = self._urlOpener.GET(GOOGLE_AJAX_SEARCH_URL + params)
            except:
                raise w3afException('Failed to GET google.com AJAX API.')
            
            # Parse the response. Convert the json string into a py dict.
            parsed_resp = json.loads(resp.getBody())

            # Expected response code is 200; otherwise raise Exception
            if parsed_resp.get('responseStatus') != 200:
                raise w3afException(parsed_resp.get('responseDetails'))

            # Update results list
            result_list += [googleResult(res['url']) for res in \
                                parsed_resp['responseData']['results']]
            # Update result pages
            res_pages.append(resp)

            # Update 'start' and continue loop
            start += GOOGLE_AJAX_MAX_RES_PER_PAGE

        return result_list[:count], res_pages

    
    def met_search(self, query, start=0, count=10):
        """
        Search the web with Google.
        
        @return: A tuple with two lists, one of google result objects, the second one is a list of httpResponses
        """
        results = []
        res_pages = []
        # TODO: Update this, it changes!!
        regex_string = '<h\d class="r"><a href="(.*?)" class=l'
        max_start = start + count
        
        while start < max_start:
            params = urllib.urlencode({'hl': 'en', 'q': query,
                                       'start': start, 'sa': 'N'})
            
            response = self._urlOpener.GET(GOOGLE_SEARCH_URL + params,
                                           headers=self._headers,
                                           useCache=True,
                                           grepResult=False)
            
            # Remember that httpResponse objects have a faster "__in__" than
            # the one in strings; so string in response.getBody() is slower than
            # string in response
            if 'http://www.google.com/support/bin/answer.py?answer=86640' in response:
                raise w3afException('Google is telling us to stop doing automated tests.')
                
            # Save the result page
            res_pages.append(response)

            for url in re.findall(regex_string, response.getBody()):
                # Parse the URL
                url = urllib.unquote_plus( url )
                
                # Google returns (not always) a result that doesn't have a protocol
                # we add a default protocol (http)
                if not url.startswith('https://') and \
                    not url.startswith('ftp://') and \
                    not url.startswith('http://'):
                    url = 'http://' + url
                    
                # Save the results
                results.append(googleResult(url))
            
            start += 10

        return results[:count], res_pages

class googleResult:
    '''
    This is a dummy class that represents a search engine result.
    '''    
    def __init__( self, url ):
        self.URL = url



