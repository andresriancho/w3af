# -*- coding: UTF-8 -*-
'''
baseparser.py

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
import urllib

from core.data.constants.encodings import UTF8
from core.data.parsers.encode_decode import htmldecode
from core.data.parsers.urlParser import url_object
from core.controllers.misc.encoding import is_known_encoding


class BaseParser(object):
    '''
    This class is an abstract document parser.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    #URL_RE = ('((http|https):[A-Za-z0-9/](([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%'
    #    '[A-Fa-f0-9]{2})+(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?)')
    URL_RE = re.compile(
                    '((http|https)://([\w:@\-\./]*?)[^ \n\r\t"\'<>]*)', re.U)
    RELATIVE_URL_RE = re.compile(
        '((:?[/]{1,2}[\w\-~\.%]+)+\.\w{2,4}(((\?)([\w\-~\.%]*=[\w\-~\.%]*)){1}'
        '((&)([\w\-~\.%]*=[\w\-~\.%]*))*)?)', re.U)
    EMAIL_RE = re.compile(
                    '([\w\.%-]{1,45}@([A-Z0-9\.-]{1,45}\.){1,10}[A-Z]{2,4})',
                    re.I|re.U)
    SAFE_CHARS = (('\x00', '%00'),)

    # Matches
    # "PHP/5.2.4-2ubuntu5.7", "Apache/2.2.8", "mod_python/3.3.1"
    # used in _find_relative() method
    PHP_VERSION_RE = re.compile('.*?/\d\.\d\.\d')
    
    
    def __init__(self, httpResponse):
        
        encoding = httpResponse.getCharset()
        if not is_known_encoding( encoding ):
            raise ValueError('Unknown encoding: %s' % encoding)
        
        # "setBaseUrl"
        url = httpResponse.getURL()
        redirURL = httpResponse.getRedirURL()
        if redirURL:
            url = redirURL
        
        self._baseUrl = url
        self._baseDomain = url.getDomain()
        self._rootDomain = url.getRootDomain()
        self._encoding = httpResponse.getCharset()
        
        # To store results
        self._emails = []
        self._re_urls = set()

    def getEmails(self, domain=None):
        '''
        @param domain: Indicates what email addresses I want to retrieve.
                       All are returned if the domain is not set.
                       
        @return: A list of email accounts that are inside the document.
        
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse( 200, '', {}, u, u )
        >>> a = BaseParser(response)
        >>> a._emails = ['a@w3af.com', 'foo@not-w3af.com']
        
        >>> a.getEmails()
        ['a@w3af.com', 'foo@not-w3af.com']

        >>> a.getEmails( domain='w3af.com')
        ['a@w3af.com']

        >>> a.getEmails( domain='not-w3af.com')
        ['foo@not-w3af.com']
                
        '''
        if domain:
            return [i for i in self._emails if domain == i.split('@')[1]]
        else:
            return self._emails
            
    def getForms(self):
        '''
        @return: A list of forms.
        '''        
        raise NotImplementedError('You should create your own parser class '
                                  'and implement the getForms() method.')
        
    def getReferences(self):
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
        raise NotImplementedError('You should create your own parser class '
                                  'and implement the getReferences() method.')
        
    def getComments(self):
        '''
        @return: A list of comments.
        '''        
        raise NotImplementedError('You should create your own parser class '
                                  'and implement the getComments() method.')
    
    def getScripts(self):
        '''
        @return: A list of scripts (like javascript).
        '''        
        raise NotImplementedError('You should create your own parser class '
                                  'and implement the getScripts() method.')
        
    def getMetaRedir(self):
        '''
        @return: Returns list of meta redirections.
        '''
        raise NotImplementedError('You should create your own parser class '
                                  'and implement the getMetaRedir() method.')
    
    def getMetaTags(self):
        '''
        @return: Returns list of all meta tags.
        '''
        raise NotImplementedError('You should create your own parser class '
                                  'and implement the getMetaTags() method.')
    
    def _findEmails(self, doc_str):
        '''
        @return: A list with all mail users that are present in the doc_str.

        Init,
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse( 200, '', {}, u, u )
        >>> a = BaseParser(response)
        
        First test, no emails.
        >>> a._findEmails( '' )
        []
        
        >>> a = BaseParser(response)
        >>> a._findEmails(u' abc@w3af.com ')
        [u'abc@w3af.com']
        
        >>> a = BaseParser(response)
        >>> a._findEmails(u'<a href="mailto:abc@w3af.com">test</a>')
        [u'abc@w3af.com']

        >>> a = BaseParser(response)
        >>> a._findEmails(u'<a href="mailto:abc@w3af.com">abc@w3af.com</a>')
        [u'abc@w3af.com']

        >>> a = BaseParser(response)
        >>> a._findEmails(u'<a href="mailto:abc@w3af.com">abc_def@w3af.com</a>')
        [u'abc@w3af.com', u'abc_def@w3af.com']

        >>> a = BaseParser(response)
        >>> a._findEmails(u'header abc@w3af-scanner.com footer')
        [u'abc@w3af-scanner.com']
        
        >>> a = BaseParser(response)
        >>> a._findEmails(u'header abc4def@w3af.com footer')
        [u'abc4def@w3af.com']
        '''
        
        # Revert url-encoded sub-strings
        doc_str = urllib.unquote_plus(doc_str)
        
        # Then html-decode HTML special characters
        doc_str = htmldecode(doc_str)
        
        # Perform a fast search for the @. In w3af, if we don't have an @ we
        # don't have an email
        # We don't support emails like myself <at> gmail !dot! com
        if doc_str.find('@') != -1:
            compiled_re = re.compile('[^\w@\-\\.]', re.UNICODE)
            doc_str = re.sub(compiled_re, ' ', doc_str)
            for email, domain in re.findall(self.EMAIL_RE, doc_str):
                if email not in self._emails:
                    self._emails.append(email)
            
        return self._emails
    
    def _regex_url_parse(self, doc_str):
        '''
        Use regular expressions to find new URLs.
        
        @param httpResponse: The http response object that stores the
            response body and the URL.
        @return: None. The findings are stored in self._re_urls as url_objects

        Init,
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse(200, '', {}, u, u)

        Simple, empty result
        >>> a = BaseParser(response)
        >>> response = httpResponse(200, '', {}, u, u)
        >>> a._regex_url_parse(response.body)
        >>> len(a._re_urls)
        0
        
        Full URL
        >>> a = BaseParser(response)
        >>> a._regex_url_parse(u'header http://www.w3af.com/foo/bar/index.html footer')
        >>> url_object('http://www.w3af.com/foo/bar/index.html') in a._re_urls
        True

        One relative URL
        >>> a = BaseParser(response)
        >>> a._regex_url_parse(u'header /foo/bar/index.html footer')
        >>> url_object('http://www.w3af.com/foo/bar/index.html') in a._re_urls
        True

        >>> a = BaseParser(response)
        >>> a._regex_url_parse(u'header /subscribe.aspx footer')
        >>> url_object('http://www.w3af.com/subscribe.aspx') in a._re_urls
        True

        Relative with initial "/" , inside an href
        >>> a = BaseParser(response)
        >>> a._regex_url_parse(u'header <a href="/foo/bar/index.html">foo</a> footer')
        >>> url_object('http://www.w3af.com/foo/bar/index.html') in a._re_urls
        True

        Simple index relative URL
        >>> a = BaseParser(response)
        >>> a._regex_url_parse(u'header <a href="index">foo</a> footer')
        >>> len(a._re_urls)
        0
        '''
        re_urls = self._re_urls
        
        for url in self.URL_RE.findall(doc_str):
            # This try is here because the _decode_url method raises an
            # exception whenever it fails to decode a url.
            try:
                decoded_url = url_object(self._decode_url(url[0]),
                                         encoding=self._encoding)
            except ValueError:
                pass
            else:
                re_urls.add(decoded_url)
        
        re_urls.update(self._find_relative(doc_str))
        
        # Finally, normalize the urls
        map(lambda u: u.normalizeURL(), re_urls)    
    
    def _filter_false_urls(self, potential_url):
        potential_url = potential_url[0]
        if potential_url.startswith('//') or \
            potential_url.startswith('://') or \
            potential_url.startswith('HTTP/') or \
            self.PHP_VERSION_RE.match( potential_url ):
            return False
        
        return True
    
    def _find_relative(self, doc_str):
        '''
        
        Now detect some relative URL's (also using regexs)
        
        '''
        res = set()
        filter_false_urls = self._filter_false_urls
        
        # TODO: Also matches //foo/bar.txt and http://host.tld/foo/bar.txt
        # I'm removing those matches manually below
        for match_tuple in filter( filter_false_urls, self.RELATIVE_URL_RE.findall(doc_str) ):
            
            match_str = match_tuple[0]
                        
            try:
                url = self._baseUrl.urlJoin(match_str).url_string
                url = url_object(self._decode_url(url),
                                 encoding=self._encoding)
            except ValueError:
                # In some cases, the relative URL is invalid and triggers an 
                # ValueError: Invalid URL "%s" exception. All we can do at this
                # point is to ignore this "fake relative URL".
                pass
            else:
                url_lower = url.url_string.lower()
                if url_lower.startswith('http://') or url_lower.startswith('https://'):
                    res.add(url)
        
        return res
        
    def _decode_url(self, url_string):
        '''
        Decode `url_string` using urllib's url-unquote
        algorithm. The returned value is always a unicode string. 
        
        See http://www.blooberry.com/indexdot/html/topics/urlencoding.htm for
        more info on urlencoding.
        
        So, when _decode_url() is called and take as input 
        u'http://host.tld/%05%44', it is encoded using the instance's _encoding
        then it is applied the unquote routine and finally is decoded back to
        unicode being u'http://host.tld/é' the final result.
        
        Something small to remember:
        >>> urllib.unquote('ind%c3%a9x.html').decode('utf-8').encode('utf-8') \
        == 'ind\xc3\xa9x.html'
        True
        
        Init,
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> response = httpResponse(200, u'', {}, u, u, charset='latin1')
        >>> a = BaseParser(response)
        >>> a._encoding = 'latin1'
        
        Simple, no strange encoding
        >>> a._decode_url(u'http://www.w3af.com/index.html')
        u'http://www.w3af.com/index.html'

        Encoded
        >>> a._decode_url(u'http://www.w3af.com/ind%E9x.html') == \
        u'http://www.w3af.com/ind\xe9x.html'
        True
        
        Decoding of safe chars skipped ('\x00' and ' ')
        >>> a._decode_url(u'http://w3af.com/search.php?a=%00x&b=2%20c=3%D1') ==\
        u'http://w3af.com/search.php?a=%00x&b=2 c=3\xd1'
        True
        
        Ignoring possible decoding errors
        >>> a._encoding = 'utf-8'
        >>> a._decode_url(u'http://w3af.com/blah.jsp?p=SQU-300&bgc=%FFAAAA')
        u'http://w3af.com/blah.jsp?p=SQU-300&bgc=AAAA'
        '''
        enc = self._encoding

        if isinstance(url_string, unicode):
            url_string = url_string.encode(enc)
                
        dec_url = urllib.unquote(url_string)
        for sch, repl in self.SAFE_CHARS:
            dec_url = dec_url.replace(sch, repl)
        
        # Always return unicode
        # TODO: Any improvement for this? We're certainly losing
        # information by using the 'ignore' error handling
        
        try:
            dec_url = dec_url.decode(UTF8)
        except UnicodeDecodeError:
            dec_url = dec_url.decode(enc, 'ignore')
        #
        # TODO: Lines below will remain commented until we make a
        # decision regarding which is the (right?) way to decode URLs.
        # The tests made on FF and Chrome revealed that if strange
        # (i.e. non ASCII) characters are present in a URL the browser
        # will urlencode the URL string encoded until the beginning
        # of the query string using the page charset and the query 
        # string itself encoded in UTF-8.
        #
        # Apparently this is not a universal practice. We've found
        # some static sites having URL's encoded *only* in Windows-1255
        # (hebrew) for example.
        #
        # This is what de W3C recommends (not a universal practice though):
        #    http://www.w3.org/TR/REC-html40/appendix/notes.html#h-B.2
        #
##        index = dec_url.find('?')
##        if index > -1:
##            dec_url = (dec_url[:index].decode(enc, 'ignore') +
##                       dec_url[index:].decode('utf-8', 'ignore'))
        
        return dec_url
