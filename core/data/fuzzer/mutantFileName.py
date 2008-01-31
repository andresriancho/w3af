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

    def getMutantType( self ):
        return 'filename'

    def setDoubleEncoding( self, trueFalse ):
        self._doubleEncoding = trueFalse
        
    def getURL( self ):
        url = self._freq.getURL()
        # Please note that this double encoding is needed if we want to work with mod_rewrite
        encoded = urllib.quote_plus( self._dc['fuzzedFname'] )
        if self._doubleEncoding:
            encoded = urllib.quote_plus( encoded )
        return  url + self._dc['start'] + encoded + self._dc['end']
        
    getURI = getURL
    
    def getData( self ):
        return ''
    
    def printModValue( self ):
        return 'The sent '+ self.getMutantType() +' is: "' + self._dc['start'] + self._dc['fuzzedFname'] + self._dc['end'] + '" .'
        
    def setModValue( self, val ):
        self._dc['fuzzedFname'] = val
    
    def setURL( self, u ):
        raise w3afException('You can\'t change the value of the URL in a mutantFileName instance.')

    def dynamicURL( self ):
        '''
        The URL will change, don't try to use it to avoid reporting something more than once.
        '''
        return True
