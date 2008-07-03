'''
abstractParser.py

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

import core.data.parsers.urlParser as urlParser
from core.data.parsers.encode_decode import htmldecode
import re
import urllib

class abstractParser:
    '''
    This class is an abstract document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self, baseUrl ):
        # "setBaseUrl"
        self._baseUrl = baseUrl
        self._baseDomain = urlParser.getDomain(baseUrl)
        self._rootDomain = urlParser.getRootDomain(baseUrl)
        self._emails = []
    
    def findAccounts( self , documentString ):
        '''
        @return: A list with all mail users that are present in the documentString.
        '''
        # First, we decode all chars. I have found some strange sites where they encode the @... some other
        # sites where they encode the email, or add some %20 padding... strange stuff... so better be safe...
        documentString = urllib.unquote_plus( documentString )
        
        # Now we decode the html special characters...
        documentString = htmldecode( documentString )
        
        # Perform a fast search for the @. In w3af, if we don't have an @ we don't have an email
        # We don't support mails like myself <at> gmail !dot! com
        if documentString.find('@') != -1:
            documentString = re.sub( '[^\w@\\.]', ' ', documentString )
            
            # Now we have a clean documentString; and we can match the mail addresses!
            emailRegex = '(([\w\._]+)@('+self._rootDomain+'|'+self._baseDomain+'))'
            for email, username, host in re.findall(emailRegex, documentString):
                if email not in self._emails:
                    self._emails.append( email )
                    
        return self._emails

    def getAccounts( self ):
        '''
        @return: A list of email accounts that are inside the document.
        '''
        raise Exception('You should create your own parser class and implement the getAccounts() method.')
    
    def getForms( self ):
        '''
        @return: A list of forms.
        '''        
        raise Exception('You should create your own parser class and implement the getForms() method.')
        
    def getReferences( self ):
        '''
        @return: A list of URL strings.
        '''        
        raise Exception('You should create your own parser class and implement the getReferences() method.')
        
    def getComments( self ):
        '''
        @return: A list of comments.
        '''        
        raise Exception('You should create your own parser class and implement the getComments() method.')
    
    def getScripts( self ):
        '''
        @return: A list of scripts (like javascript).
        '''        
        raise Exception('You should create your own parser class and implement the getScripts() method.')
        
    def getMetaRedir( self ):
        '''
        @return: Returns list of meta redirections.
        '''
        raise Exception('You should create your own parser class and implement the getMetaRedir() method.')
    
    def getMetaTags( self ):
        '''
        @return: Returns list of all meta tags.
        '''
        raise Exception('You should create your own parser class and implement the getMetaTags() method.')
        
