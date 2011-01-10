'''
mutantCookie.py

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

from core.data.fuzzer.mutant import mutant
from core.controllers.w3afException import w3afException


class mutantCookie(mutant):
    '''
    This class is a headers mutant.
    '''
    def __init__( self, freq ):
        mutant.__init__(self, freq)

    def getMutantType( self ):
        return 'cookie'

    def getURL( self ):
        '''
        The next methods (getURL and getURI) are really simple, but they override the URL creation algorithm of httpQsRequest, that
        uses the self._dc variable. If I don't have these methods, I end up with something like this:
        
        ========================================Request 15 - Sat Oct 27 21:05:34 2007========================================
        GET http://localhost/w3af/cookieFuzzing/cf.php?domain=%3CSCRIPT%3Ealert2%28%27bzbbw1R8AJ9ALQEM5jKI50fZn%27%29%3C%2FSCRIPT%3E HTTP/1.1
        Host: localhost
        Cookie: path=/~rasmus/; domain=<SCRIPT>alert2('bzbbw1R8AJ9ALQEM5jKI50fZn')</SCRIPT>; expires=Sun, 28-Oct-2007 01:05:34 GMT; TestCookie=something+from+somewh
        Accept-encoding: identity
        Accept: */*
        User-agent: w3af.sourceforge.net
        '''
        return self._url
    
    def getURI( self ):
        return self._uri

    def setDc( self, c ):
        self.setCookie( c )
        
    def getDc( self ):
        return self.getCookie()
        
    def getData( self ):
        return ''
    
    def setModValue( self, val ):
        '''
        Set the value of the variable that this mutant modifies.
        '''
        try:
            self._freq._cookie[ self.getVar() ][ self._index ] = val
        except Exception, e:
            raise w3afException('The cookie mutant object wasn\'t correctly initialized.')
        
    def getModValue( self ): 
        try:
            return self._freq._cookie[ self.getVar() ][ self._index ]
        except:
            raise w3afException('The cookie mutant object was\'nt correctly initialized.')
            
    def foundAt(self):
        '''
        @return: A string representing WHAT was fuzzed. This string is used like this:
                - v.setDesc( 'SQL injection in a '+ v['db'] +' was found at: ' + mutant.foundAt() )
        '''
        res = ''
        res += '"' + self.getURL() + '", using HTTP method '
        res += self.getMethod() + '. The modified parameter was the session cookie with value: "'
        
        # Depending on the data container, print different things:
        dc_length = 0
        for i in self._freq._dc:
            dc_length += len(i) + len(self._freq._dc[i])
        if dc_length > 65:
            res += '...' + self.getVar()  + '=' + self.getModValue() + '...'
            res += '"'
        else:
            res += str(self.getDc())
            res += '".'
        
        return res       
