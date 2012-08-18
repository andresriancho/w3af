'''
mutantUrlParts.py

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

from core.data.fuzzer.mutant import mutant
from core.controllers.w3afException import w3afException

class mutantUrlParts(mutant):
    '''
    This class is a urlparts mutant.
    '''
    def __init__( self, freq ):
        mutant.__init__(self, freq)
        self._doubleEncoding = False
        self._safeEncodeChars = ''

    def getMutantType( self ):
        return 'urlparts'

    def setDoubleEncoding( self, trueFalse ):
        self._doubleEncoding = trueFalse
    
    def setSafeEncodeChars( self, safeChars ):
        '''
        @parameter safeChars: A string with characters we don't want to URL encode in the urlparts. Example:
            - '/&!'
            - '/'
        '''
        self._safeEncodeChars = safeChars
    
    def getURL( self ):
        '''
        @return: The URL, as modified by "setModValue()"
        
        >>> from core.data.parsers.urlParser import url_object
        >>> from core.data.request.fuzzable_request import fuzzable_request
        >>> from core.data.dc.dataContainer import DataContainer
        >>> divided_path = DataContainer()
        >>> divided_path['start'] = '/'
        >>> divided_path['fuzzedUrlParts'] = 'ping!'
        >>> divided_path['end'] = '/def'
        
        >>> fr = fuzzable_request(url_object('http://www.w3af.com/abc/def'))        
        >>> m = mutantUrlParts( fr )
        >>> m.setMutantDc(divided_path)
        >>> m.setVar('fuzzedUrlParts')
        >>> m.getURL().url_string
        u'http://www.w3af.com/ping%21/def'
        '''
        domain_path = self._freq.getURL().getDomainPath()
        
        # Please note that this double encoding is needed if we want to work with mod_rewrite
        encoded = urllib.quote_plus( self._mutant_dc['fuzzedUrlParts'], self._safeEncodeChars )
        if self._doubleEncoding:
            encoded = urllib.quote_plus( encoded, safe=self._safeEncodeChars )
        domain_path.setPath( self._mutant_dc['start'] + encoded + self._mutant_dc['end'] )
        return domain_path
        
    getURI = getURL
    
    def getData( self ):
        return None
    
    def printModValue( self ):
        res = 'The sent '+ self.getMutantType() +' is: "' + self._mutant_dc['start']
        res += self._mutant_dc['fuzzedUrlParts'] + self._mutant_dc['end'] + '" .'
        return res
        
    def setModValue( self, val ):
        self._mutant_dc['fuzzedUrlParts'] = val
        
    def getModValue(self):
        return self._mutant_dc['fuzzedUrlParts']
    
    def setURL( self, u ):
        raise w3afException('You can\'t change the value of the URL in a mutantUrlParts instance.')

    def foundAt(self):
        '''
        @return: A string representing WHAT was fuzzed. This string is used like this:
                - v.setDesc( 'SQL injection in a '+ v['db'] +' was found at: ' + mutant.foundAt() )
        '''
        res = ''
        res += '"' + self.getURL() + '", using HTTP method '
        res += self.getMethod() + '. The fuzzed parameter was the target URL, with value: "'
        res += self.getModValue() + '".'
        return res
