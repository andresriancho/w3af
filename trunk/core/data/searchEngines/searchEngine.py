'''
searchEngine.py

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

from core.controllers.w3afException import w3afException
from  core.controllers import outputManager as om



class searchEngine:
    '''
    This class represents a searchEngine .
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        self._headers = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)'}

    def getNResults(self, query, limit=0):
        '''
        Return a list of URLs ; that represent the result to all the search.
        '''
        start = 0
        result = []
        while True:
            try:
                tmp = self.search(query, start, 10)
            except w3afException, w3:
                om.out.debug(str(w3))
                raise
            except Exception, e:
                msg = 'An unhandled exception was found in ' \
                'searchEngines.searchEngine.search(): "%s"' % str(e)
                om.out.error(msg)
                raise w3afException(msg)
            else:
                result += tmp
                start += len(tmp)
                if len(tmp) != 10 or start >= limit:
                    break

        # Do some debug..
        if result:
            om.out.debug('Search engine result: ')
            for res in result:
                om.out.debug('- ' + res.URL)
        else:
            om.out.debug('Search engine returned no results.')

        return result

    def getNResultPages(self, query, limit=0):
        '''
        Return a list of httpresponses that represent the pages returned by
        the search engine when w3af performs a search.
        '''
        start = 0
        result = []
        while True:
            try:
                res_page = self.page_search(query, start, 10)
            except w3afException, w3:
                om.out.debug(str(w3))
                raise
            except Exception, e:
                om.out.debug('Unhandled exception in searchEngines.searchEngine.search(): ' + str(e))
                raise
            else:
                result.extend(res_page)
                start += 10
                if start >= limit:
                    break

        return result

    def numberOfResults(self, query):
        '''
        Return the number of results for a given search.
        '''
        number_of_results = 0
        while True:
            res = self.search(query, number_of_results, 10)
            number_of_results += len(res)
            if len(res) != 10:
                break

        return number_of_results

    def search(self, query, start, count=10):
        '''
        This method is meant to be overriden by the subclasses of searchEngine.py
        
        This method searches the web and returns a list of URLs.
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''
        raise w3afException('searchEngine subclasses should implement the search method.')

    def page_search(self, query, start, count=10):
        '''
        This method is meant to be overriden by the subclasses of searchEngine.py
        
        This method searches the web and returns a list of http response objects.
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''
        raise w3afException('searchEngine subclasses should implement the page_search method.')


