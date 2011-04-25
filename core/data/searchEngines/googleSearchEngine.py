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
try:
    import json
except:
    import extlib.simplejson as json

from core.controllers import outputManager as om
from core.controllers.w3afException import w3afException

from core.data.searchEngines.searchEngine import searchEngine
from core.data.parsers.urlParser import url_object


GOOGLE_SORRY_PAGE = 'http://www.google.com/support/bin/answer.py?answer=86640'
# Set the order in which the Google API searchers will be called by the 
# googleSearchEngine
GOOGLE_PRIORITY_SEARCH_SEQ = ('GAjaxSearch', 'GMobileSearch',
                              'GStandardSearch',)

class googleSearchEngine(searchEngine):
    '''
    This class is a wrapper for doing google searches. It allows the user to do GET requests
    to the mobile version, the Ajax API and the standard www.google.com page.
    
    @author: Andres Riancho (andres.riancho@gmail.com), floyd fuh (floyd_fuh@yahoo.de)
    '''
    
    def __init__(self, url_opener):
        searchEngine.__init__(self)
        # url_opener's GET wrapper function
        self._url_open = lambda url: url_opener.GET(
                                            url, headers=self._headers,
                                            useCache=True, grepResult=False)
    
    def getNResults(self, query, limit=0):
        return self.search(query, 0, count=limit)
        
    def search(self, query, start, count=10):
        '''
        Perform a google search and return the resulting links (URLs).
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''
        return self._do_ordered_search(query, start, count)
    
    def page_search(self, query, start, count=10):
        '''
        Perform a *standard* google search and return the google result 
        pages (HTML).
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''        
        return GStandardSearch(self._url_open, query, start, count).pages
        
    def _do_ordered_search(self, query, start, count):
        '''
        Do the Google search by calling the Google API searchers in the order
        specified in GOOGLE_PRIORITY_SEARCH_SEQ
        '''
        res = []
        _globals = globals()
        curr_count = count

        for search_class_str in GOOGLE_PRIORITY_SEARCH_SEQ:
           
            g_search_class = _globals[search_class_str]
            g_searcher = g_search_class(self._url_open, query, 
                                        start, curr_count)
            res += g_searcher.links
            len_res = len(res)
            start += len_res
            curr_count -= len_res
            if len_res >= count:
                break
        
        om.out.debug("Google search for: '%s' returned %s results." % \
                            (query, len(res)))
        om.out.debug("Google search for: '%s' returned %s results." % \
                            (query, len(set(res))))
        return res
        
    
    def set(self, word_list):
        '''
        Performs a google set search.
        http://labs.google.com/sets
        '''
        google_search_set = GSetSearch(self, word_list)
        return google_search_set.set



IS_NEW = 0
FINISHED_OK = 1
FINISHED_BAD = 2
##THERE_IS_MORE = 3

class GoogleAPISearch(object):
    '''
    'Abstract' base class for the Google API search implementations. This class
    shouldn't be instantiated.
    '''
    
    def __init__(self, url_open_func):
        '''
        @parameter url_open_func: function to call by this class to do the
        request. Accepts 'url' as param and returns a httpResponse object.
        '''
        self._status = IS_NEW
        self._url_open_func = url_open_func
        # list of httpResponse objects
        self._pages = []
        # list of URLs
        self._links = []
    
    @property
    def status(self):
        return self._status

    @property
    def pages(self):
        if self._status == IS_NEW:
            try:
                self._pages = self._do_google_search()
            except Exception, e:
                self._status = FINISHED_BAD
            else:
                self._status = FINISHED_OK
        return self._pages

    @property
    def links(self):
        if self._status == IS_NEW:
            self._links = self._extract_links(self.pages)

        return self._links

    def _do_GET(self, url):
        if not isinstance(url, url_object):
            msg = 'The url parameter of a _do_GET  must'
            msg += ' be of urlParser.url_object type.'
            raise ValueError( msg )
        
        return self._url_open_func(url)

    def _do_google_search(self):
        '''
        Perform the google search based on implementation. This method has
        to be overriden by subclasses.
        '''
        pass


    def _extract_links(self, pages):
        '''
        Return list of URLs found in pages. Must be overriden by subclasses.
        '''
        pass


class GAjaxSearch(GoogleAPISearch):
    '''
    Search the web using Google's AJAX API. Note that Google restricts
    this API to return only the first 64 results.
    '''
    
    GOOGLE_AJAX_SEARCH_URL = "http://ajax.googleapis.com/ajax/services/search/web?"
    GOOGLE_AJAX_MAX_RES_PER_PAGE = 8
    GOOGLE_AJAX_MAX_START_INDEX = 56

    def __init__(self, url_open_func, query, start=0, count=10):
        '''
        @parameter query: query to perform
        @parameter start: start index.
        @parameter count: amount of results to fetch
        '''
        GoogleAPISearch.__init__(self, url_open_func)
        self._query = query
        self._start = start
        self._count = count
    
    def _do_google_search(self):
        
        res_pages = []        
        start = self._start
        max_start = min(start + self._count,
                        self.GOOGLE_AJAX_MAX_START_INDEX + 
                        self.GOOGLE_AJAX_MAX_RES_PER_PAGE)

        while start < max_start:
            size = min(max_start - start, self.GOOGLE_AJAX_MAX_RES_PER_PAGE)
            
            # Build param dict; then encode it
            params_dict = {'v': '1.0', 'q': self._query,
                           'rsz': size, 'start': start}
            params = urllib.urlencode(params_dict)
            
            google_url_instance = url_object(self.GOOGLE_AJAX_SEARCH_URL + params)
            
            # Do the request
            try:
                resp = self._do_GET( google_url_instance )
            except:
                raise w3afException('Failed to GET google.com AJAX API.')
            
            # Parse the response. Convert the json string into a py dict.
            parsed_resp = json.loads(resp.getBody())

            # Expected response code is 200; otherwise raise Exception
            if parsed_resp.get('responseStatus') != 200:
                raise w3afException(parsed_resp.get('responseDetails'))

            # Update result pages
            res_pages.append(resp)

            # Update 'start' and continue loop
            start += self.GOOGLE_AJAX_MAX_RES_PER_PAGE

        return res_pages

    def _extract_links(self, pages):
        links = []

        for page in pages:
            # Update results list
            parsed_page = json.loads(page.getBody())
            links += [googleResult( url_object( res['url'] ) ) for res in \
                        parsed_page['responseData']['results']]
        return links[:self._count]
    
    
class GStandardSearch(GoogleAPISearch):
    '''
    Search the web with standard Google webpage.
    '''
    
    GOOGLE_SEARCH_URL = "http://www.google.com/search?"
    
    # TODO: Update this, it changes!!
    REGEX_STRING = '<h\d class="r"><a href="(.*?)" class=l'
    # Used to find out if google will return more items
    NEXT_PAGE_REGEX = 'id=pnnext.*?\>\<span.*?\>\</span\>\<span.*?\>Next\<'
    
    def __init__(self, url_open_func, query, start=0, count=10):
        '''
        @parameter query: query to perform
        @parameter start: start index.
        @parameter count: amount of results to fetch
        '''
        GoogleAPISearch.__init__(self, url_open_func)
        self._query = query
        self._start = start
        self._count = count

    def _do_google_search(self):
        res_pages = []
        
        start = self._start
        max_start = start + self._count
        there_is_more = True
        
        while start < max_start  and there_is_more:
            params = urllib.urlencode({'hl': 'en', 'q': self._query,
                                       'start': start, 'sa': 'N'})
            
            google_url_instance = url_object(self.GOOGLE_SEARCH_URL + params)
            response = self._do_GET( google_url_instance )
            
            # Remember that httpResponse objects have a faster "__in__" than
            # the one in strings; so string in response.getBody() is slower than
            # string in response
            if GOOGLE_SORRY_PAGE in response:
                raise w3afException(
                      'Google is telling us to stop doing automated tests.')
            if not self._has_more_items(response.getBody()):
                there_is_more = False

            # Save the result page
            res_pages.append(response)
            
            start += 10

        return res_pages
    
    def _extract_links(self, pages):
        links = []
        
        for resp in pages:
            for url in re.findall(self.REGEX_STRING, resp.getBody()):
                # Parse the URL
                url = urllib.unquote_plus(url)
                
                # Google sometimes returns a result that doesn't have a
                # protocol we add a default protocol (http)
                if not url.startswith('https://') and \
                    not url.startswith('ftp://') and \
                    not url.startswith('http://'):
                    url = 'http://' + url
                    
                # Save the links
                links.append( googleResult( url_object(url) ) )

        return links[:self._count]
    
    def _has_more_items(self, google_page_text):
        x = re.search(self.NEXT_PAGE_REGEX, google_page_text, 
                        re.IGNORECASE)
        return x is not None


class GMobileSearch(GStandardSearch):
    '''
    Search the web using Google's Mobile search. Note that Google doesn't
    restrict the access to this page right now.
    '''
    GOOGLE_SEARCH_URL = "http://www.google.com/m?"
    
    #Match stuff like (without line breaks)
    #<a href="/gwt/x?dc=gorganic&amp;q=site:microsoft.com&amp;hl=en&amp;
    #ei=PtqqTJjfMaO4jAeCkIrXAw&amp;ved=0CAsQFjAD&amp;start=0&amp;
    #output=wml&amp;source=m&amp;rd=1&amp;u=http://www.microsoft.com/dynamics/">Microsoft
    REGEX_STRING = '&amp;source=m&amp;rd=1&amp;u=(.*?)"\s?>'
    # Used to find out if google will return more items.
    # TODO: This changes. Check it!
    NEXT_PAGE_REGEX = '\<a href=".*?" \>Next page'
    
    
    def __init__(self, url_open_func, query, start=0, count=10):
        '''
        @parameter url_open_func: function to call by this class to do the
            request. Accepts 'url' as param and returns a httpResponse 
            object.
        @parameter query: query to perform
        @parameter start: start index.
        @parameter count: amount of results to fetch
        '''
        GoogleAPISearch.__init__(self, url_open_func)
        self._query = query
        self._start = start
        self._count = count    

    def _do_google_search(self):
        
        start = self._start
        res_pages = []
        max_start = start + self._count
        param_dict = {'dc': 'gorganic', 'hl': 'en', 'q': self._query,
                      'sa': 'N', 'source': 'mobileproducts'}
        there_is_more = True
        
        while start < max_start and there_is_more:
            param_dict['start'] = start
            params = urllib.urlencode(param_dict)
            gm_url = self.GOOGLE_SEARCH_URL + params
            gm_url_instance = url_object(gm_url)
            response = self._do_GET( gm_url_instance )               
            
            if GOOGLE_SORRY_PAGE in response:
                raise w3afException(
                      'Google is telling us to stop doing automated tests.')
            
            if not self._has_more_items(response.getBody()):
                there_is_more = False
            
            res_pages.append(response)                          
            start += 10

        return res_pages
    

class GSetSearch(GoogleAPISearch):
    
    GOOGLE_SEARCH_URL = "http://labs.google.com/sets?hl=en"
    REGEX = '<font face="Arial, sans-serif" size=-1>' \
            '<a href="http://www.google.com/search\?hl=en&amp;q=(.*?)">'
    
    def __init__(self, url_open_func, word_list):
        GoogleAPISearch.__init__(self, url_open_func, None)
        self._word_list = word_list
        self._set = []

    @property
    def set(self):
        if self.status == IS_NEW:
            self._set = self._extract_set(self.pages)
        return self._set

    def _do_google_search(self):
        '''
        Performs a google set search.
        http://labs.google.com/sets
        '''
        
        results = []
        
        if self._word_list:
            # I'll use the first 5 inputs
            _word_list = self._word_list[:5]
        
            # This is a search for a set with input blue and white
            # http://labs.google.com/sets?hl=en&q1=blue&q2=white&q3=&q4=
            #&q5=&btn=Small+Set+%2815+items+or+fewer%29
            url = self.GOOGLE_SEARCH_URL
            q_param = 1
            
            for word in _word_list:
                url += '&q' + str(q_param) + '=' + urllib.quote_plus(word)
                q_param += 1

            url += '&btn=Small+Set+%2815+items+or+fewer%29'
            url_instance = url_object( url )
            # Now I get the results
            response = self._do_GET(url_instance)
            results.append(response)

        return results
    
    def _extract_set(self, pages):
        word_set = []
        for resp in pages:            
            for word in re.findall(self.REGEX, resp.getBody()):
                word = urllib.unquote_plus(word.lower())
                if word not in self._word_list:
                    word_set.append(word)
        
        om.out.debug('Google set search returned:')
        for i in word_set:
            om.out.debug('- ' + i )

        return word_set    


class googleResult(object):
    '''
    This is a dummy class that represents a search engine result.
    '''    
    def __init__(self, url):
        if not isinstance(url, url_object):
            msg = 'The url __init__ parameter of a googleResult object must'
            msg += ' be of urlParser.url_object type.'
            raise ValueError( msg )

        self.URL = url

