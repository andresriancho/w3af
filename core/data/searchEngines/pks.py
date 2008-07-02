'''
pks.py

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
from core.data.searchEngines.searchEngine import searchEngine as searchEngine
import core.data.parsers.urlParser as urlParser
import urllib
import re


class pks(searchEngine):
    '''
    This class is a wrapper for doing PKS searches on the MIT PKS server. 
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, urlOpener ):
        searchEngine.__init__(self)
        self._urlOpener = urlOpener
        
    def search( self, hostname ):
    
        if hostname.count('//'):
            raise w3afException('You must provide the pks search engine with a root domain name (as returned by urlParser.getRootDomain).')
    
        res = self.met_search( hostname )
        om.out.debug('pks search for hostname : '+ hostname + ' returned ' + str( len( res ) ) + ' results.' )
        return res

    def met_search(self, query):
        """
        lookup(query) -> results

        Query a Public Key Server.
        
        This method is based from the pks.py file from the massive enumeration toolset, 
        coded by pdp and released under GPL v2.     
        """
        class pksResult:
            def __init__( self, name, username ):
                self.name = name
                self.username = username
                
        url = 'http://pgp.mit.edu:11371/pks/lookup?'
        _query = urllib.urlencode({'op':'index', 'search':query})

        response = self._urlOpener.GET(url + _query, headers=self._headers, useCache=True, grepResult=False )
        content = response.getBody()
        
        content = re.sub('(<.*?>|&lt;|&gt;)', '', content)

        results = []
        accounts = []
        
        for line in content.split('\n')[6:]:
            if not line.strip():
                continue

            tokens = line.split()
            
            email = None
            name = None
            
            if re.search('\d{4}/\d{2}/\d{2}', line):
                email = tokens[-1]
                name = ' '.join(tokens[3:-1])
            else:
                email = tokens[-1]
                name = ' '.join(tokens[:-1])
            
            account = email.split('@')[0]
            if not account.count('*'):  # This kills revokated lines
                if name != None and email != None and account not in accounts:
                    pksr = pksResult( name, account )
                    results.append( pksr )
                    accounts.append( account )

        return results
    
