'''
bing.py

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

import urllib
import re

import core.controllers.outputManager as om
from core.data.searchEngines.searchEngine import searchEngine as searchEngine

class bing(searchEngine):
    '''
    This class is a wrapper for doing bing searches. It allows the user to use pymsn or simply do GET requests
    to bing.com.

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, urlOpener):
        searchEngine.__init__(self)
        self._urlOpener = urlOpener

    def search(self, query, start, count=10):
        res = self._metSearch(query, start)
        om.out.debug('Bing search for: ' + query + ' returned ' + str(len(res)) + ' results.')
        return res

    def _metSearch(self, query, start=0):
        '''
        Search the web with Bing.

        This method is based from the msn.py file from the massive enumeration toolset,
        coded by pdp and released under GPL v2.
        '''
        class bingResult:
            '''
            Dummy class that represents the search result.
            '''
            def __init__( self, url ):
                self.URL = url

        url = 'http://www.bing.com/search?'
        _query = urllib.urlencode({'q':query, 'first':start+1, 'FORM':'PERE'})
        response = self._urlOpener.GET(url+_query, headers=self._headers,
                useCache=True, grepResult=False)
        results = []

        # This regex MAY become outdated
        urls = re.findall('<h3><a href="(.*?)" onmousedown', response.getBody())

        if len(urls) == 11:
            urls = urls[:-1]

        for url in urls:
            if 'www.bing.com' not in url:
                results.append(bingResult(url))
        return results
