'''
httpResponse.py

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


import copy
import re
import httplib
from lxml import etree

import core.controllers.outputManager as om
from core.data.parsers.urlParser import url_object

# Handle codecs
import codecs
def _returnEscapedChar(exc):
    slash_x_XX = repr(exc.object[exc.start:exc.end])[1:-1]
    return ( unicode(slash_x_XX) , exc.end)
codecs.register_error("returnEscapedChar", _returnEscapedChar)


DEFAULT_CHARSET = 'utf-8'
CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '

class httpResponse(object):
    

    def __init__(self, code, read, info, geturl, original_url,
                 msg='OK', id=None, time=0.2, alias=None):
        '''
        @parameter time: The time between the request and the response.
        '''
        if not isinstance(geturl, url_object):
            raise ValueError('The geturl.__init__() parameter of a httpResponse object must be of urlParser.url_object type.')

        if not isinstance(original_url, url_object):
            raise ValueError('The original_url.__init__() parameter of a httpResponse object must be of urlParser.url_object type.')
        
        # A nice and comfortable default
        self._charset = 'utf-8'
        self._content_type = ''
        self._dom = None
        self._clear_text_body = None
        
        # Set the URL variables
        # The URL that we really GET'ed
        self._realurl = original_url.uri2url()
        self._uri = original_url
        # Set the info
        self._info = info
        # The URL where we were redirected to (equal to original_url when no redirect)
        self._redirectedURL = geturl
        self._redirectedURI = geturl.uri2url()
        
        # Set the rest
        self.setCode(code)

        # Save the type for fast access, so I don't need to calculate the type each time
        # someone calls the "is_text_or_html" method. This attributes are set in the
        # setHeaders() method.
        self._is_text_or_html_response = False
        self._is_swf_response = False
        self._is_pdf_response = False
        self._is_image_response = False
        self.setHeaders(info)
        
        self.setBody(read)
        self._msg = msg
        self._time = time
        self._alias = alias
        
        # A unique id identifier for the response
        self.id = id

        self._fromCache = False
        
    
    def getId( self ): return self.id
    def getRedirURL( self ): return self._redirectedURL
    def getRedirURI( self ): return self._redirectedURI
    def getCode( self ): return self._code
    def getAlias(self): return self._alias
    def getBody( self ): return self._body
    def info(self): return self._info

    def getClearTextBody(self):
        '''
        @return: A clear text representation of the HTTP response body. 
        '''
        
        if self._clear_text_body is not None:
            #
            #    We already calculated this, we can return it now.
            #
            return self._clear_text_body
        else:
            #
            #    Calculate the clear text body
            #
            dom = self.getDOM()
            
            if dom is None:
                # return None if we don't have a DOM
                return None
                
            else:
                self._clear_text_body = ''
                
                for elem in dom.getiterator():
                    
                    if elem.tag == 'br':
                        self._clear_text_body += '\n'
                    else:
                        # get the text
                        text = elem.text
                        if text is not None:
                            self._clear_text_body += text
                
                return self._clear_text_body

    
    def getDOM(self):
        '''
        I don't want to calculate the DOM for all responses, only for those
        which are needed. This method will first calculate the DOM, and then
        save it for upcoming calls.
        
        @return: The DOM, or None if the HTML normalization failed.
        '''
        if self._dom is None:
            try:
                parser = etree.HTMLParser(recover=True)
                self._dom = etree.fromstring(self._body, parser)
            except Exception:
                msg = 'The HTTP body for "%s" could NOT be ' \
                'parsed by libxml2.' % self.getURL()
                om.out.debug(msg)
        return self._dom
    
    def getNormalizedBody(self):
        '''
        @return: A normalized body
        '''
        dom = self.getDOM()
        if dom is not None:
            return etree.tostring(dom, encoding=self._charset)
        return None
    
    def getHeaders( self ): return self._headers
    def getLowerCaseHeaders( self ):
        '''
        If the original headers were:
            'Abc-Def: f00N3s'
        This will return:
            'abc-def: f00N3s'
        
        The only thing that changes is the header name.
        '''
        res = {}
        for i in self._headers:
            res[ i.lower() ] = self._headers[ i ]
        return res
        
    def getURL( self ): return self._realurl
    def getURI( self ): return self._uri
    def getWaitTime( self ): return self._time
    def getMsg( self ): return self._msg
    def getCharset(self): return self._charset
    
    def setRedirURL( self, ru ): self._redirectedURL = ru
    def setRedirURI( self, ru ): self._redirectedURI = ru
    def setCode( self, code ): self._code = code
    def setBody( self, body):
        '''
        This method decodes the body based on the header(or metadata) encoding and
        afterwards, it creates the necesary metadata to speed up string searches inside
        the body string.

        @body: A string that represents the body of the HTTP response
        @return: None
        '''
        #   Sets the self._body attribute
        self._charset_handling(body)
        
    def __contains__(self, string_to_test):
        '''
        Determine if any of the strings inside the string_list match the HTTP response body.

        @parameter string_list: The list of strings
        '''
        return string_to_test in self._body

    def _charset_handling(self, body):
        '''
        This method decodes the body based on the header(or metadata) encoding.
        
        This is one of the most important methods, because it will decode any string
        (usually HTTP response body contents) and return an utf-8 encoded string. In other words,
        this methods does c14n (Canonicalization) (http://en.wikipedia.org/wiki/Canonicalization)
        and allows all layers of w3af to simply ignore the encoding of the HTTP body (if that's
        what they want).        

        @body: A string that represents the body of the HTTP response
        @return: None
        '''
        # A sample header just to remember how they look like: "content-type: text/html; charset=iso-8859-1"
        lowerCaseHeaders = self.getLowerCaseHeaders()
        if not 'content-type' in lowerCaseHeaders:
            om.out.debug('hmmm... wtf?! The remote web server failed to send the content-type header.')
            self._body = body
        else:
            if not self.is_text_or_html():
                # Not text, save as it is.
                self._body = body
            else:
                # According to the web server, the body content is text, html, xml or something similar
                
                # I'll get the charset from the response headers, and the charset from the HTML content meta tag
                # if the charsets differ, then I'll decode the text with one encoder, and then with the other; comparing
                # which of the two generated less encoding errors. The one with less encoding errors is going to be
                # set as the self._body variable.
                
                # Go for the headers
                headers_charset = ''
                re_charset = re.findall('charset=([\w-]+)', lowerCaseHeaders['content-type'] )
                if re_charset:
                    # well... it seems that they are defining a charset in the response headers..
                    headers_charset = re_charset[0].lower().strip()
                    
                # Now go for the meta tag
                # I parse <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> ?
                meta_charset = ''
                re_charset = re.findall('<meta.*?content=".*?charset=([\w-]+)".*?>', body, re.IGNORECASE )
                if re_charset:
                    # well... it seems that they are defining a charset in meta tag...
                    meta_charset = re_charset[0].lower().strip()
                
                # by default we asume:
                charset = DEFAULT_CHARSET
                if meta_charset == '' and headers_charset != '':
                    charset = headers_charset
                elif headers_charset == '' and meta_charset != '':
                    charset = meta_charset
                elif headers_charset == meta_charset and headers_charset != '':
                    charset = headers_charset
                elif meta_charset != headers_charset:
                    om.out.debug('The remote web application sent charset="'+ headers_charset + '" in the header, but charset="' +\
                    meta_charset +'" in the HTML body meta tag. Using the HTML charset.')
                    
                    # Mozilla uses the HTML charset, so I'm going to use it.
                    charset = meta_charset
                    
                # Now that we have the charset, we use it! (and save it)
                # The return value of the decode function is a unicode string.
                try:
                    unicode_str = body.decode(charset, 'returnEscapedChar')
                except LookupError:
                    # warn about a buggy charset
                    msg = 'Charset LookupError: unknown charset: ' + charset
                    msg += '; ignored and set to default: ' + self._charset
                    om.out.debug( msg )
                    
                    # Use the default
                    charset = DEFAULT_CHARSET
                    unicode_str = body.decode(charset, 'returnEscapedChar')
               
                # Now we use the unicode_str to create a utf-8 string that will be used in all w3af
                self._body = unicode_str.encode('utf-8')
                
                # And we save the charset, just in case.
                self._charset = charset

    def setHeaders( self, headers ):
        '''
        Sets the headers and also analyzes them in order to get the response mime type (text/html , application/pdf, etc).

        @parameter headers: The headers dict.
        '''
        # Fix lowercase in header names from HTTPMessage
        if isinstance(headers, httplib.HTTPMessage):
            self._headers = {}
            for header in headers.headers:
                key, value = header.split(':', 1)
                self._headers[key.strip()] = value.strip()
        else:
            self._headers = headers

        #   Set the type, for easy access.
        for key in headers.keys():
            if 'content-type' == key.lower():
                # we need exactly content type but not charset
                self._content_type = headers[key].split(';', 1)[0]
                
                #   Text or HTML?
                magic_words = ['text', 'html', 'xml', 'txt', 'javascript']
                for mw in magic_words:
                    if self._content_type.lower().count(mw):
                        self._is_text_or_html_response = True
                        return

                #   PDF?
                if self._content_type.lower().count('pdf'):
                    self._is_pdf_response = True
                
                #   SWF?
                if self._content_type.lower().count('x-shockwave-flash'):
                    self._is_swf_response = True

                #   Image?
                if self._content_type.lower().count('image'):
                    self._is_image_response = True

    def getContentType( self ):
        '''
        @return: The content type of the response
        '''
        return self._content_type

    def is_text_or_html( self ):
        '''
        @return: True if this response is text or html
        '''
        return self._is_text_or_html_response
    
    def is_pdf( self ):
        '''
        @return: True if this response is a PDF file
        '''
        return self._is_pdf_response
    
    def is_swf( self ):
        '''
        @return: True if this response is a SWF file
        '''
        return self._is_swf_response

    def is_image( self ):
        '''
        @return: True if this response is an image file
        '''
        return self._is_image_response
            
    def setURL( self, url ):
        '''
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURL('http://www.google.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The URL of a httpResponse object must be of urlParser.url_object type.
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURL( url_object('http://www.google.com/') )
        '''
        if not isinstance(url, url_object):
            raise ValueError('The URL of a httpResponse object must be of urlParser.url_object type.')
        
        self._realurl = url.uri2url()
    
    def setURI( self, uri ):
        '''
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURI('http://www.google.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: The URI of a httpResponse object must be of urlParser.url_object type.
        >>> u = url_object('http://www.google.com')
        >>> r = httpResponse(200, '' , {}, u, u)
        >>> r.setURI( url_object('http://www.google.com/') )
        '''
        if not isinstance(uri, url_object):
            raise ValueError('The URI of a httpResponse object must be of urlParser.url_object type.')
        
        self._uri = uri
        self._realurl = uri.uri2url()
        
    def setWaitTime( self, t ): self._time = t

    def getFromCache(self):
        '''
        @return: True if this response was obtained from the local cache.
        '''
        return self._fromCache
        
    def setFromCache(self, fcache):
        '''
        @parameter fcache: True if this response was obtained from the local cache.
        '''
        self._fromCache = fcache

    def __repr__( self ):
        res = '< httpResponse | %s | %s ' % ( self.getCode() , self.getURL() )

        # extra info
        if self.id is not None:
            res += ' | id:'+str(self.id)

        if self._fromCache != False:
            res += ' | fromCache:True'

        # aaaand close...
        res += ' >'
        return res

    def getStatusLine(self):
        '''Return status-line of response.'''
        return 'HTTP/1.1' + SP + str(self._code) + SP + self._msg + CRLF

    def dumpResponseHead( self ):
        '''
        @return: A string with:
            HTTP/1.1 /login.html 200
            Header1: Value1
            Header2: Value2
        '''
        strRes = self.getStatusLine()
        strRes += self.dumpHeaders()
        return strRes

    def dump( self ):
        '''
        Return a DETAILED str representation of this HTTP response object.
        '''
        strRes = self.dumpResponseHead()
        strRes += CRLF
        strRes += self.getBody()
        return strRes
        
    def dumpHeaders( self ):
        '''
        @return: a str representation of the headers.
        '''
        strRes = ''
        for header in self._headers:
            strRes += header + ': ' + self._headers[ header ] + CRLF
        return strRes
        
    def copy( self ):
        return copy.deepcopy( self )


