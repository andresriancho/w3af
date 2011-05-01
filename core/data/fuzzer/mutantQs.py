'''
mutantQs.py

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


class mutantQs(mutant):
    '''
    This class is a query string mutant.
    '''
    def __init__( self, freq ):
        mutant.__init__(self, freq)
    
    def getMutantType( self ):
        return 'query string'
    
    def printModValue( self ):
        '''
        >>> from core.data.parsers.urlParser import url_object
        >>> from core.data.request.fuzzableRequest import fuzzableRequest
        >>> freq = fuzzableRequest()
        >>> u = url_object('http://www.w3af.com/')
        >>> freq.setURL( u )
        >>> m = mutantQs( freq )
        >>> m.printModValue()
        'The sent URI was http://www.w3af.com/ .'
        '''
        return 'The sent URI was '+ self.getURI() +' .'
    
