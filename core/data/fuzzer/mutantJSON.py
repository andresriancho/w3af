'''
mutantJSON.py

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

from core.data.fuzzer.mutantPostData import mutantPostData

class mutantJSON(mutantPostData):
    '''
    This class is a JSON mutant.
    '''
    def __init__( self, freq ):
        mutantPostData.__init__(self, freq)

    def getMutantType( self ):
        return 'JSON data'

    def foundAt(self):
        '''
        I had to implement this again here instead of just inheriting from mutantPostData because
        of the duplicated parameter name support which I added to the framework.
        
        @return: A string representing WHAT was fuzzed. This string is used like this:
                - v.setDesc( 'SQL injection in a '+ v['db'] +' was found at: ' + mutant.foundAt() )
        '''
        res = ''
        res += '"' + self.getURL() + '", using HTTP method '
        res += self.getMethod() + '. The sent JSON-data was: "'
        res += str(self.getDc())
        res += '"'
        return res
