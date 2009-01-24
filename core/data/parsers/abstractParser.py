# -*- coding: utf-8 -*-
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

import core.controllers.outputManager as om
import core.data.parsers.urlParser as urlParser
from core.data.parsers.encode_decode import htmldecode
from core.controllers.w3afException import w3afException

import re
import urllib


class abstractParser:
    '''
    This class is an abstract document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self, httpResponse ):
        # "setBaseUrl"
        url = httpResponse.getURL()
        redirURL = httpResponse.getRedirURL()
        if redirURL:
            url = redirURL
        self._baseUrl = urlParser.getDomainPath(url)
        self._baseDomain = urlParser.getDomain(url)
        self._rootDomain = urlParser.getRootDomain(url)
        
        # A nice default
        self._encoding = 'utf-8'
        
        # To store results
        self._emails = []
        self._re_URLs = []
    
    def findEmails( self , documentString ):
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
            emailRegex = '([A-Z0-9\._%-]{1,45}@([A-Z0-9\.-]{1,45}\.){1,10}[A-Z]{2,4})'
            for email, domain in re.findall(emailRegex, documentString,  re.IGNORECASE):
                if email not in self._emails:
                    self._emails.append( email )
                    
        return self._emails

    def _regex_url_parse(self, httpResponse):
        '''
        Use regular expressions to find new URLs.
        
        @parameter httpResponse: The http response object that stores the response body and the URL.
        @return: None. The findings are stored in self._re_URLs.
        '''
        #url_regex = '((http|https):[A-Za-z0-9/](([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%[A-Fa-f0-9]{2})+(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?)'
        url_regex = '((http|https)://([\w\./]*?)/[^ \n\r\t"<>]*)'
        for url in re.findall(url_regex, httpResponse.getBody() ):
            # This try is here because the _decodeString method raises an exception
            # whenever it fails to decode a url.
            try:
                decoded_url = self._decodeString(url[0], self._encoding)
            except w3afException:
                pass
            else:
                self._re_URLs.append(decoded_url)
        
        # Now detect some relative URL's ( also using regexs )
        def find_relative( doc ):
            res = []
            # TODO: Also matches //foo/bar.txt , which is bad
            # I'm removing those matches manually below
            relative_regex = re.compile('[A-Z0-9a-z%_~\./]+([\/][A-Z0-9a-z%_~\.]+)+\.[A-Za-z0-9]{1,5}(((\?)([a-zA-Z0-9]*=\w*)){1}((&)([a-zA-Z0-9]*=\w*))*)?')
            
            while True:
                regex_match = relative_regex.search( doc )
                if not regex_match:
                    break
                else:
                    s, e = regex_match.span()
                    match_string = doc[s:e]
                    if not match_string.startswith('//'):
                        domainPath = urlParser.getDomainPath(httpResponse.getURL())
                        url = urlParser.urlJoin( domainPath , match_string )
                        url = self._decodeString(url)
                        res.append( url )
                    
                    # continue
                    doc = doc[e:]
            return res
        
        relative_URLs = find_relative( httpResponse.getBody() )
        self._re_URLs.extend( relative_URLs )
        self._re_URLs = [ urlParser.normalizeURL(i) for i in self._re_URLs ]
        self._re_URLs = list(set(self._re_URLs))
        
        '''
        om.out.debug('Relative URLs found using regex:')
        for u in self._re_URLs:
            if '8_' in u:
                om.out.information('! ' + u )
        '''    

    def getEmails( self, domain=None ):
        '''
        @parameter domain: Indicates what email addresses I want to retrieve:   "*@domain".
        @return: A list of email accounts that are inside the document.
        '''
        if domain:
            return [ i for i in self._emails if domain in i.split('@')[1] ]
        else:
            return self._emails
    def getForms( self ):
        '''
        @return: A list of forms.
        '''        
        raise Exception('You should create your own parser class and implement the getForms() method.')
        
    def getReferences( self ):
        '''
        Searches for references on a page. w3af searches references in every html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.
        
        @return: Two sets, one with the parsed URLs, and one with the URLs that came out of a
        regular expression. The second list if less trustworthy.
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
        
    def _decodeString(self, string_to_decode, encoding='utf-8'):
        '''
        >>> print urllib.unquote('ind%c3%a9x.html').decode('utf-8').encode('utf-8')
        indéx.html
        '''
        try:
            return urllib.unquote(string_to_decode).decode(encoding).encode('utf-8')
        except UnicodeDecodeError, ude:
            # This error could have been produced by the buggy choice of encoding
            # done by the user when calling _decodeString with two parameters, 
            # or "selected by default". So, now we are going to test something different
            if encoding == 'utf-8':
                # Test an encoding that only uses one byte:
                return urllib.unquote(string_to_decode).decode('iso-8859-1').encode('utf-8')
            else:
                msg = 'Failed to _decodeString: "' + string_to_decode +'" using encoding: ' + encoding
                om.out.error(msg)
                raise w3afException(msg)
