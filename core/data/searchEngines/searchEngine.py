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
import socket
import re
import core.controllers.outputManager as om

class searchEngine:
    '''
    This class represents a searchEngine .
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__( self ):
        self._headers = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)'}
    
    def getNResults( self, query, limit=0 ):
        '''
        Return a list of URLs ; that represent the result to all the search.
        '''
        start = 0
        result = []
        while True:
            try:
                tmp = self.search( query, start, 10 )
            except w3afException, w:
                om.out.debug( str(w) )
                return result
            except Exception, e:
                om.out.debug( 'Unhandled exception in searchEngines.google.search(): '+str(w) )
                return result
            else:
                result.extend( tmp )
                start += len( tmp )
                if len( tmp ) != 10 or start >= limit: break
        
        # Do some debug..
        if len( result ):
            om.out.debug('Search engine result: ')
            for res in result:
                om.out.debug('- ' + res.URL )
        else:
            om.out.debug('Search engine returned no results.')
            
        return result
    
    def getNResultPages( self, query, limit=0 ):
        '''
        Return a list of httpresponses that represent the pages returned by the search engine when
        w3af performs a search.
        '''
        start = 0
        result = []
        while True:
            try:
                resPage = self.pagesearch( query, start, 10 )
            except w3afException, w:
                om.out.debug( str(w) )
                return result
            except Exception, e:
                om.out.debug( 'Unhandled exception in searchEngines.google.search(): '+str(w) )
                return result
            else:
                result.extend( resPage )
                start += 10
                if start >= limit: break
    
        return result
        
    def numberOfResults( self, query ):
        '''
        Return the number of results for a given search.
        '''
        numberOfResults = 0
        while True:
            res = self.search( query, numberOfResults, 10 )
            numberOfResults += len( res )
            if len( res ) != 10: break
            
        return numberOfResults
        
    def search( self, query, start, count=10 ):
        raise w3afException('searchEngine subclasses should implement the search method.')

    def isPrivate( self, dp ):
        '''
        Get the IP address of the domain, return True if its a private address.
        '''
        if re.match('(10\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', dp) or\
        re.match('(172\.[1-3]\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', dp) or\
        re.match('(192\.168\.\d?\d?\d?\.\d?\d?\d?)', dp) or\
        re.match('(127\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', dp):
            return True
        else:
            addrinfo = None
            try:
                addrinfo = socket.getaddrinfo(dp, 0)
            except:
                raise w3afException('Could not resolve hostname: ' + dp )
            ips = [info[4][0] for info in addrinfo]
            for ip in ips:
                if re.match('(10\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', ip) or\
                re.match('(172\.[1-3]\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', ip) or\
                re.match('(192\.168\.\d?\d?\d?\.\d?\d?\d?)', ip) or\
                re.match('(127\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)', ip):
                    return True
        return False
