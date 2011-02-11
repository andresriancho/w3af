# -*- coding: UTF-8 -*-
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


class abstractParser(object):
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
        self._baseUrl = url
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
            
            # NOTE: emailRegex is also used in pks search engine.
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
        url_regex = '((http|https)://([a-zA-Z0-9_:@\-\./]*?)/[^ \n\r\t"\'<>]*)'
        for url in re.findall(url_regex, httpResponse.getBody() ):
            # This try is here because the _decode_URL method raises an exception
            # whenever it fails to decode a url.
            try:
                decoded_url = self._decode_URL(url[0], self._encoding)
            except w3afException:
                pass
            else:
                self._re_URLs.append(decoded_url)
        
        #
        # Now detect some relative URL's ( also using regexs )
        #
        def find_relative( doc ):
            res = []
            
            # TODO: Also matches //foo/bar.txt and http://host.tld/foo/bar.txt
            # I'm removing those matches manually below
            regex = '((:?[/]{1,2}[A-Z0-9a-z%_\-~\.]+)+\.[A-Za-z0-9]{2,4}(((\?)([a-zA-Z0-9]*=\w*)){1}((&)([a-zA-Z0-9]*=\w*))*)?)'
            relative_regex = re.compile( regex )
            
            for match_tuple in relative_regex.findall(doc):
                
                match_string = match_tuple[0]
                
                #
                #   And now I filter out some of the common false positives
                #
                if match_string.startswith('//'):
                    continue
                    
                if match_string.startswith('://'):
                    continue

                if re.match('HTTP/\d\.\d', match_string):
                    continue
                
                # Matches "PHP/5.2.4-2ubuntu5.7" , "Apache/2.2.8", and "mod_python/3.3.1"
                if re.match('.*?/\d\.\d\.\d', match_string):
                    continue
                #
                #   Filter finished.
                #
                    
                domainPath = urlParser.getDomainPath(httpResponse.getURL())
                url = urlParser.urlJoin( domainPath , match_string )
                url = self._decode_URL(url, self._encoding)
                res.append( url )
            
            return res
        
        relative_URLs = find_relative( httpResponse.getBody() )
        self._re_URLs.extend( relative_URLs )
        self._re_URLs = [ urlParser.normalizeURL(i) for i in self._re_URLs ]
        self._re_URLs = list(set(self._re_URLs))
        

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
        
    def _decode_URL(self, url_to_decode, encoding):
        '''
        This is one of the most important methods, because it will decode any URL
        and return an utf-8 encoded string. In other words, this methods does c14n (Canonicalization)
        (http://en.wikipedia.org/wiki/Canonicalization) and allows all layers of w3af to simply ignore the
        encoding of the HTTP body (if that's what they want).
        
        This method is very related to httpResponse._charset_handling(), which decodes the HTTP
        body of the response. The "problem" is that the body of the response is decoded as expected,
        but URLs aren't... why? Let's see an example:
        
        - HTTP Body: <a href="http://host.tld/%05%44">Click m\x05\x44!</a>
        - HTTP response header indicated encoding: xyz
        - After running _charset_handling() and supposing that "\x05\x44" decodes to "é" in xyz,
        the response is: <a href="http://host.tld/%05%44">Click mé!</a>
        
        As you may have noticed, the %05%44 (which in URL means "\x05\x44") wasn't decoded
        (as expected because the decoding method doesn't handle URL encoding AND xyz encoding at the
        same time!).
        
        So, when we use _decode_URL() we take as input "http://host.tld/%05%44", we decode the
        URL encoding to get "http://host.tld/\x05\x44" and finally we decode that with the xyz encoding
        to get "http://host.tld/é".
        
        Something small to remember:
        >>> urllib.unquote('ind%c3%a9x.html').decode('utf-8').encode('utf-8') == 'ind\xc3\xa9x.html'
        True
        '''
        
        # Avoid the double decoding performed by httpResponse._charset_handling() and
        # by this function in the cases like this link:
        #
        #   http://host.tld/é.html
        #
        # Which is written without URL encoding.
        if urllib.unquote(url_to_decode) == url_to_decode:
            return url_to_decode
            
        try:
            return urllib.unquote(url_to_decode).decode(encoding).encode('utf-8')
        except UnicodeDecodeError, ude:
            # This error could have been produced by the buggy choice of encoding
            # done by the user when calling _decode_URL with two parameters, 
            # or "selected by default". So, now we are going to test something different
            if encoding == 'utf-8':
                # Test an encoding that only uses one byte:
                return urllib.unquote(url_to_decode).decode('iso-8859-1').encode('utf-8')
            elif encoding != 'utf-8':
                # Sometimes, the web app developers, their editors, or some other component
                # makes a mistake, and they are really encoding it with utf-8 and they say they are
                # doing it with some other encoding; this is why I perform this last test:
                try:
                    return urllib.unquote(url_to_decode).decode('utf-8').encode('utf-8')
                except UnicodeDecodeError, ude:
                    msg = 'Failed to _decode_URL: "' + url_to_decode +'" using encoding: "' + encoding + '".'
                    om.out.error(msg)
                    raise ude
