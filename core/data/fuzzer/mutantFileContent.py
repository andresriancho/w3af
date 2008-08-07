'''
mutantFileContent.py

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

class mutantFileContent(mutant):
    '''
    This class is a filename mutant.
    '''
    def __init__( self, freq ):
        mutant.__init__(self, freq)

    def getMutantType( self ):
        return 'filename'

    def getData( self ):
        '''
        Override the default getData() of the fuzzable request that contains a str(self._dc) <<---- that kills the
        file I contain in my DC.
        '''
        return self._dc
    
    def foundAt(self):
        '''
        @return: A string representing WHAT was fuzzed. This string is used like this:
                - v.setDesc( 'SQL injection in a '+ v['db'] +' was found at: ' + mutant.foundAt() )
        '''
        res = ''
        res += '"' + self.getURL() + '", using HTTP method '
        res += self.getMethod() + '. The sent data was: "'
        
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
        
        res +=' The modified parameter was the file content with value: "' + self.getVar() +'".'
        
        return res
