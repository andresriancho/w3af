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
        # http://search.yahooapis.com/SiteExplorerService/V1/pageData?appid=YahooDemo&query=http://search.yahoo.com&results=2
        url = 'http://search.yahooapis.com/SiteExplorerService/V1/pageData?'
        _query = urllib.urlencode({'appid':'YahooDemo', 'query':query, 'results':count , 'start': start+1})

        response = self._urlOpener.GET(url + _query, headers=self._headers, useCache=True, grepResult=False )
        
        results = []

        for url in re.findall('<Url>(.*?)</Url>', response.getBody() ):
            yserInstance = yahooSiteExplorerResult( url )
            results.append( yserInstance )

        return results

class yahooSiteExplorerResult:
    '''
    This is a dummy class that represents a search engine result.
    '''
    def __init__( self, url ):
        self.URL = url
