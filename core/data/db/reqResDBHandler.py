'''
reqResDBHandler.py

Copyright 2007 Andres Riancho

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

import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
import re
from core.controllers.w3afException import w3afException
   
class reqResDBHandler:
    '''
    A handler for the database that stores requests and responses.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        pass
    
    def _initDB( self ):
        try:
            self._db_req_res = kb.kb.getData('gtkOutput', 'db')
        except:
            return False
        else:
            return True
    
    def searchById( self, search_id ):
        '''
        @return: A request object that has an id == search_id
        '''
        def bruteforceSearch( id ):
            # Bruteforce search
            try:
                result = [ r for r in self._db_req_res if r.id == search_id ][0]
            except Exception, e:
                return None
            else:
                return result
        
        if not self._initDB():
            raise w3afException('The database is not initialized yet.')
        else:
            try:
                # Search by """"primary key""""
                result = self._db_req_res[ int(search_id) - 1 ]
            except:
                return bruteforceSearch( search_id )
            else:
                # pk search went ok, verify result.
                if result.id != search_id:
                    om.out.debug('Something wierd happened with the numbering of the requests.... doing bruteforce search.')
                    return bruteforceSearch( search_id )
                else:
                    return result
                    
    def validate(self, text):
        '''
        Validates if the text matches the regular expression
        
        @param text: the text to validate
        @return: True if the text is ok.
        '''
        ### WARNING !!!!
        ### Remember that this regex controls what goes into a exec() function, so, THINK about what you are doing before allowing some characters
        self._match = re.match('^(?:((?:r\\.(?:id|method|uri|http_version|request_headers|data|code|msg|response_headers|body))) (==|>|>=|<=|<|!=) ([\w\'\" /:\.]+)( (and|or) )?)*$', text )
        ### WARNING !!!!
        if self._match:
            return True
        else:
            return False
            
    def searchByString( self, search_string ):
        '''
        @return: A request object that matches the search string.
        '''
        if not self._initDB():
            raise w3afException('The database is not initialized yet.')
        else:
            if not self.validate( search_string ):
                # The text that was entered by the user is not a valid search!
                raise w3afException('Invalid search string.')
            else:
                return self._doSearch( search_string )

    def _doSearch( self, condition ):
        '''
        Perform a search where only one (request of response) database is involved
        '''
        toExec = 'resultList = [ r for r in self._db_req_res if %s ]' % condition
        
        try:
            # FIXME: This should have a different globals and locals
            exec( toExec )
        except:
            raise w3afException('Invalid search string, please try again.')
        else:
            return resultList
    
