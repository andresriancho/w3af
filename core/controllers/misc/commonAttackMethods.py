'''
commonAttackMethods.py

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

class commonAttackMethods:
    def __init__( self ):
        pass
        
    def setCut( self, header, footer ):
        self._header = header
        self._footer = footer
    
    def getCut( self ):
        return self._header, self._footer
        
    def _defineCut( self, body, expectedResult, exact=True ):
        '''
        Defines the section where the result of an attack will be.
        For example, when doing a local File Include attack, the included file could
        be in the middle of some HTML text, so a regex is created to cut the important
        part out of a simple html.
        
        @return: True if the cut could be defined
        '''
        if body.count( expectedResult ):
            headerEnd = body.find( expectedResult )
            if exact:
                footerStart = headerEnd + len( expectedResult )
                if footerStart == len( body ):
                    footerStart = -1
            else:
                footerStart = body.find( '<', headerEnd )
            self._header = body[:headerEnd]
            
            if footerStart == -1:
                self._footer = 'EOBody'
            else:
                self._footer = body[footerStart:len(body)]
            
            om.out.debug('Defined cut header as: "' + self._header + '"')
            om.out.debug('Defined cut footer as: "' + self._footer + '"')
            
            return True
        else:
            return False
    
    def _cut( self, body ):
        '''
        After defining a cut, I can cut parts of an HTML and return the important
        sections.
        '''
        if body == '':
            om.out.debug('Called _cut with an empty body to cut, returning an empty result.')
            return body
            
        if self._footer != 'EOBody':
            if body.rfind(self._footer) == -1:
                # hmmm , test one more time...
                # this kludge is to fix some \n or \r issues
                if body.rfind(self._footer[1:]) == -1:
                    raise w3afException('An error ocurred. The command result footer wasnt found.')
                else:
                    result = body[ len(self._header) : body.rfind(self._footer[1:]) ]
            else:
                result = body[ len(self._header) : body.rfind(self._footer) ]
            return result
        else:
            result = body[ len(self._header) : ]
            return result
    
