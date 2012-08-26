'''
mutantFileName.py

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

class mutantFileName(mutant):
    '''
    This class is a filename mutant.
    '''
    def __init__( self, freq ):
        mutant.__init__(self, freq)
        self._doubleEncoding = False
        self._safeEncodeChars = ''

    def getMutantType( self ):
        return 'filename'

    def setDoubleEncoding( self, trueFalse ):
        self._doubleEncoding = trueFalse
    
    def setSafeEncodeChars( self, safeChars ):
        '''
        @parameter safeChars: A string with characters we don't want to URL encode in the filename. Example:
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
        >>> divided_file_name = DataContainer()
        >>> divided_file_name['start'] = ''
        >>> divided_file_name['fuzzedFname'] = 'ping!'
        >>> divided_file_name['end'] = '.html'
        
        >>> fr = fuzzable_request(url_object('http://www.w3af.com/abc/def.html'))        
        >>> m = mutantFileName( fr )
        >>> m.setMutantDc(divided_file_name)
        >>> m.setVar( 'fuzzedFname' )
        >>> m.getURL().url_string
        u'http://www.w3af.com/abc/ping%21.html'
        '''
        domain_path = self._freq.getURL().getDomainPath()
        
        # Please note that this double encoding is needed if we want to work with mod_rewrite
        encoded = urllib.quote_plus( self._mutant_dc['fuzzedFname'], self._safeEncodeChars )
        if self._doubleEncoding:
            encoded = urllib.quote_plus( encoded, safe=self._safeEncodeChars )
        
        domain_path.setFileName( self._mutant_dc['start'] + encoded + self._mutant_dc['end'] )
        return domain_path
        
    getURI = getURL
    
    def getData( self ):
        return None
    
    def printModValue( self ):
        res = 'The sent '+ self.getMutantType() +' is: "' + self._mutant_dc['start']
        res += self._mutant_dc['fuzzedFname'] + self._mutant_dc['end'] + '" .'
        return res
        
    def setModValue( self, val ):
        self._mutant_dc['fuzzedFname'] = val
        
    def getModValue(self):
        return self._mutant_dc['fuzzedFname']
    
    def setURL( self, u ):
        raise w3afException('You can\'t change the value of the URL in a mutantFileName instance.')

    def foundAt(self):
        '''
        @return: A string representing WHAT was fuzzed. This string is used like this:
                - v.setDesc( 'SQL injection in a '+ v['db'] +' was found at: ' + mutant.foundAt() )
        '''
        res = ''
        res += '"' + self.getURL() + '", using HTTP method '
        res += self.get_method() + '. The fuzzed parameter was the target URL, with value: "'
        res += self.getModValue() + '".'
        return res
