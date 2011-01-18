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

from core.data.fuzzer.mutant import mutant
from core.controllers.w3afException import w3afException
from core.data.parsers import urlParser as urlParser
import urllib
import core.controllers.outputManager as om


class mutantFileName(mutant):
    '''
    This class is a filename mutant.
    '''
    def __init__( self, freq ):
        mutant.__init__(self, freq)
        
        self._doubleEncoding = False
        self._safeEncodeChars = ''
        self._mutant_dc = {}

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
        domain_path = urlParser.getDomainPath(self._freq.getURL())
        # Please note that this double encoding is needed if we want to work with mod_rewrite
        encoded = urllib.quote_plus( self._mutant_dc['fuzzedFname'], self._safeEncodeChars )
        if self._doubleEncoding:
            encoded = urllib.quote_plus( encoded, safe=self._safeEncodeChars )
        return  domain_path + self._mutant_dc['start'] + encoded + self._mutant_dc['end']
        
    getURI = getURL
    
    def getData( self ):
        return ''
    
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

    def dynamicURL( self ):
        '''
        The URL will change, don't try to use it to avoid reporting something more than once.
        '''
        return True

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
