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

import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException

hasPyGoogleLib = False
try:
    import extlib.pygoogle.google as pygoogle
    om.out.debug('google.py is using the bundled pygoogle library')
    hasPyGoogleLib = True
except:
    try:
        import google as pygoogle
        om.out.debug('google.py is using the systems pygoogle library')
        hasPyGoogleLib = True
    except:
        om.out.debug('google.py detected that pygoogle ain\'t installed! Doing requests manually.')
        hasPyGoogleLib = False

from core.data.searchEngines.searchEngine import searchEngine as searchEngine
import core.data.parsers.urlParser as urlParser
import urllib
import re


class googleSearchEngine(searchEngine):
    '''
    This class is a wrapper for doing google searches. It allows the user to use pygoogle or simply do GET requests
    to google.com .
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, urlOpener, key='' ):
        searchEngine.__init__(self)
        self._key = key
        self._urlOpener = urlOpener
        
    def search( self, query, start, count=10 ):
        '''
        Perform a google search and return the resulting URLs.
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''        
        if hasPyGoogleLib and self._key != '':
            pygoogle.LICENSE_KEY = self._key
            data = pygoogle.doGoogleSearch( query , start, count )
            om.out.debug('Google search for : '+ query + ' returned ' + str( len( data.results ) ) + ' results.' )
            return data.results
        else:
            # Perform requests manually
            res, resPages = self.met_search( query, start, count )
            om.out.debug('Google search for : '+ query + ' returned ' + str( len( res ) ) + ' results.' )
            return res
    
    def pagesearch( self, query, start, count=10 ):
        '''
        Perform a google search and return the google result pages.
        
        @parameter query: The query that we want to perform in the search engine
        @parameter start: The first result item
        @parameter count: How many results to get from start
        '''        
        res, resPages = self.met_search( query, start, count )
        return resPages
    
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
            #http://labs.google.com/sets?hl=en&q1=blue&q2=white&q3=&q4=&q5=&btn=Small+Set+%2815+items+or+fewer%29
            url = 'http://labs.google.com/sets?hl=en'
            q = 1
            
            for inputString in inputStringList:
                url += '&q' + str( q ) + '=' + urllib.quote_plus( inputString )
            url += '&btn=Small+Set+%2815+items+or+fewer%29'
            
            # Now I get the results
            response = self._urlOpener.GET( url , headers=self._headers, useCache=True, grepResult=False )
            
            for resultStr in re.findall('<font face="Arial, sans-serif" size=-1><a href="http://www.google.com/search\?hl=en&q=(.*?)">',response.getBody() ):
                results.append( urllib.unquote_plus( resultStr.lower() ) )
        
        results = [ x for x in results if x not in inputStringList ] 
        om.out.debug('Google set search returned:')
        for i in results:
            om.out.debug('- ' + i )
        return results
    
    def met_search(self, query, start = 0, count = 10):
        """
        search(query, start = 0, count = 10) -> results

        Search the web with Google.
        
        This method is based from the google.py file from the massive enumeration toolset, 
        coded by pdp and released under GPL v2.
        
        @return: A tuple with two lists, one of google result objects, the second one is a list of httpResponses
        """
        results = []
        resPages = []
        
        url = 'http://www.google.com/xhtml?'
        _query = urllib.urlencode({'q':query, 'start':start, 'num':count})

        response = self._urlOpener.GET(url + _query, headers=self._headers, useCache=True, grepResult=False )
        if 'href="http://www.google.com/support/bin/answer.py?answer=86640">' in response.getBody():
            raise w3afException('Google is telling us to stop doing automated tests.')
            
        resPages.append( response )
        
        for url in re.findall('<a accesskey="\d+" href="(.*?)" >',response.getBody() ):
            url = url[ url.index(';u=') + 3: ]
            url = urllib.unquote_plus( url )

            if not url.startswith('https://') and not url.startswith('ftp://') and not url.startswith('http://'):
                url = 'http://' + url

            gr = googleResult( url )
            results.append( gr )

        return results, resPages

class googleResult:
    '''
    This is a dummy class that represents a search engine result.
    '''    
    def __init__( self, url ):
        self.URL = url
