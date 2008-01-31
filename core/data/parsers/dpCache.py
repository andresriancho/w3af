'''
dpCache.py

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
import core.data.parsers.documentParser as documentParser
from core.controllers.misc.lru import LRU
import md5

class dpCache:
    '''
    This class is a document parser cache.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        self._cache = LRU(100)
        
    def getDocumentParserFor( self, document, baseUrl, normalizeMarkup=True ):
        res = None
        hash = md5.new(document).hexdigest()
        
        if hash in self._cache:
            res = self._cache[ hash ]
        else:
            # Create a new instance of dp, add it to the cache
            res = documentParser.documentParser( document, baseUrl, normalizeMarkup )
            self._cache[ hash ] = res
        
        return res
    
dpc = dpCache()
