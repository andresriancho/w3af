"""
SearchEngine.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers import output_manager as om
from w3af.core.data.dc.headers import Headers


class SearchEngine(object):
    """
    This class represents a search engine .

    :author: Andres Riancho ((andres.riancho@gmail.com))
    """

    def __init__(self):
        #
        # Based on some tests performed by Nahuel Sanchez, Google will allow
        # us to automate searches if we use this user agent:
        #
        hdrs = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36')]
        self._headers = Headers(hdrs)

    def get_n_results(self, query, limit=0):
        """
        Return a list of URLs ; that represent the result to all the search.
        """
        start = 0
        result = set()
        
        while True:
            try:
                search_results = self.search(query, start, 10)
            except BaseFrameworkException, w3:
                om.out.debug(str(w3))
                raise
            except Exception, e:
                msg = 'An unhandled exception was found in ' \
                      'search_engines.SearchEngine.search(): "%s"' % str(e)
                om.out.error(msg)
                raise BaseFrameworkException(msg)
            else:
                len_before = len(result)
                result.update(list(search_results))
                len_after = len(result)
                
                start += 10
                
                # If I keep finding new links, and the length of the result is
                # less than the limit, continue searching!
                if len_after > len_before and len(result) < limit:
                    continue
                
                break

        # Do some debug..
        if result:
            om.out.debug('Search engine result: ')
            for res in result:
                om.out.debug('- ' + res.URL)
        else:
            om.out.debug('Search engine returned no results.')

        return result

    def get_n_result_pages(self, query, limit=0):
        """
        Return a list of HTTPResponses that represent the pages returned by
        the search engine when w3af performs a search.
        """
        start = 0
        result = []

        while True:
            try:
                res_page = self.page_search(query, start, 10)
            except BaseFrameworkException, w3:
                om.out.debug(str(w3))
                raise
            except Exception, e:
                msg = ('Unhandled exception in SearchEngine.'
                       'get_n_result_pages(): "%s"')
                om.out.debug(msg % e)
                raise
            else:
                result.extend(res_page)
                start += 10
                if start >= limit:
                    break

        return result

    def number_of_results(self, query):
        """
        Return the number of results for a given search.
        """
        number_of_results = 0
        while True:
            res = self.search(query, number_of_results, 10)
            number_of_results += len(res)
            if len(res) != 10:
                break

        return number_of_results

    def search(self, query, start, count=10):
        """
        This method is meant to be overriden by the subclasses of
        SearchEngine.py

        This method searches the web and returns a list of URLs.

        :param query: The query that we want to perform in the search engine
        :param start: The first result item
        :param count: How many results to get from start
        """
        raise NotImplementedError(
            'SearchEngine subclasses should implement the search method.')

    def page_search(self, query, start, count=10):
        """
        This method is meant to be overriden by the subclasses of
        SearchEngine.py

        This method searches the web and returns a list of http response objects

        :param query: The query that we want to perform in the search engine
        :param start: The first result item
        :param count: How many results to get from start
        """
        raise NotImplementedError(
            'SearchEngine subclasses should implement the page_search method.')
