'''
yahooSiteExplorer.py

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

from core.data.searchEngines.searchEngine import searchEngine as searchEngine
from core.data.parsers.urlParser import url_object

import urllib
import re



class yahooSiteExplorer(searchEngine):
    '''
    This class is a wrapper for doing Yahoo Site Explorer searches. 
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, urlOpener ):
        searchEngine.__init__(self)
        self._urlOpener = urlOpener
        
    def search( self, query, start, count=100 ):
        '''
        This method searches the web using yahoo site explorer and returns a list of URLs.
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        ''' 
        res = self.se_search( query, start, count )
        om.out.debug('yahooSiteExplorer search for : '+ query + ' returned ' + str( len( res ) ) + ' results.' )
        return res
            
    def se_search(self, query, start = 1, count = 100):
        """
        se_search(query, start = 0, count = 10) -> results

        Search the web with yahoo Site Explorer.
        """
        # https://siteexplorer.search.yahoo.com/export?p=http%3A%2F%2Fwww.cybsec.com%2F
        url = 'https://siteexplorer.search.yahoo.com/export?p=http://'
        url += query
        url_instance = url_object(url)
        
        response = self._urlOpener.GET(url_instance, headers=self._headers, useCache=True, grepResult=False)
        
        results = []

        # The export script returns a tab separated file, parse it.
        response_body = response.getBody()
        response_body_lines = response_body.split('\n')[1:]
        for body_line in response_body_lines:
            try:
                text, url, length, content_type = body_line.split('\t')
            except Exception, e:
                msg = 'Something went wrong while parsing the YSE result line: "' + body_line + '"'
                om.out.debug( msg )
            else:
                yse_result = yahooSiteExplorerResult( url_object(url) )
                results.append( yse_result )
        
        # cut the required results
        results = results[start:start+count]
        return results

class yahooSiteExplorerResult:
    '''
    This is a dummy class that represents a search engine result.
    '''
    def __init__( self, url ):
        if not isinstance(url, url_object):
            msg = 'The url __init__ parameter of a yahooSiteExplorerResult object must'
            msg += ' be of urlParser.url_object type.'
            raise ValueError( msg )

        self.URL = url
        
    def __repr__(self):
        return '<YSE: "' + self.URL + '">'
