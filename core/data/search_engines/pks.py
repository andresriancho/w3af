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
import re

import core.controllers.outputManager as om

from core.controllers.w3afException import w3afException
from core.data.search_engines.search_engine import SearchEngine
from core.data.parsers.urlParser import url_object


class pks(SearchEngine):
    '''
    This class is a wrapper for doing PKS searches on the MIT PKS server. 
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    def __init__(self, uri_opener ):
        SearchEngine.__init__(self)
        self._uri_opener = uri_opener
        
    def search( self, hostname ):
        '''
        Searches a PKS server, and returns all emails related to hostname.
        
        @parameter hostname: The hostname from which we want to get emails from.
        '''
        if hostname.count('//'):
            msg = 'You must provide the PKS search engine with a root domain'
            msg += ' name (as returned by url_object.getRootDomain).'
            raise w3afException( msg )
    
        res = self.met_search( hostname )
        msg = 'PKS search for hostname: "%s" returned %s results.'
        om.out.debug( msg % (hostname, len(res)) )
        return res

    def met_search(self, query):
        """
        lookup(query) -> results

        Query a Public Key Server.
        
        This method is based from the pks.py file from the massive enumeration toolset, 
        coded by pdp and released under GPL v2.     
        """
        url = url_object(u'http://pgp.mit.edu:11371/pks/lookup')
        url.querystring = {u'op': u'index', u'search': query}

        response = self._uri_opener.GET( url, headers=self._headers, 
                                         cache=True, grep=False )
        content = response.getBody()
        
        content = re.sub('(<.*?>|&lt;|&gt;)', '', content)

        results = []
        accounts = []
        
        for line in content.split('\n')[2:]:
            if not line.strip():
                continue

            tokens = line.split()
            
            if len(tokens) >= 5:
                email = tokens[-1]
                name = ' '.join(tokens[3:-1])

                # Copy+paste from baseparser.py
                emailRegex = '([A-Z0-9\._%-]{1,45}@([A-Z0-9\.-]{1,45}\.){1,10}[A-Z]{2,4})'
                if re.match(emailRegex, email, re.IGNORECASE):
                    
                    account = email.split('@')[0]
                    domain = email.split('@')[1]
                    
                    if domain == query:
                        if account not in accounts:
                            pksr = PKSResult( name, account )
                            results.append( pksr )
                            accounts.append( account )

        return results
    
class PKSResult:
    def __init__( self, name, username ):
        self.name = name
        self.username = username
    
    def __repr__(self):
        return '<%s@%s>' % (self.name, self.username)
