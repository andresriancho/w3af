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
from core.data.parsers.urlParser import *

STRING_TO_IDENTIFY_ERRORS = '077b8d51aef4843c24efa7ad11ec56c6'

import codecs
def _returnEscapedChar(exc):
    slash_x_XX = repr(exc.object[exc.start:exc.end])[1:-1]
    return ( unicode(slash_x_XX) , exc.end)
def _returnStringToIdentifyError(exc):
    return ( unicode('077b8d51aef4843c24efa7ad11ec56c6') , exc.end)
    
codecs.register_error("returnEscapedChar", _returnEscapedChar)
codecs.register_error("returnStringToIdentifyError", _returnStringToIdentifyError)

import re

class httpResponse:
    
    def __init__( self, code, read , info, geturl, originalUrl, msg='OK', id=None, time=0.2):
        '''
        @parameter time: The time between the request and the response.
        '''
        self.setCode(code)
        self.setHeaders(info)
        self.setBody(read)
        
        self._realurl = uri2url( originalUrl )
        self._uri = originalUrl
        
        self._redirectedURL = geturl
        self._redirectedURI = uri2url( geturl )
        
        self._msg = msg
        # A unique id identifier for the response
        self.id = id
        self._time = time
    
    def getId( self ): return self.id
    def getRedirURL( self ): return self._redirectedURL
    def getRedirURI( self ): return self._redirectedURI
    def getCode( self ): return self._code
    def getBody( self ): return self._body
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
    
    def setRedirURL( self, ru ): self._redirectedURL = ru
    def setRedirURI( self, ru ): self._redirectedURI = ru
    def setCode( self, code ): self._code = code
    def setBody( self, body):
        
        # A sample header just to remember how they look like: "content-type: text/html; charset=iso-8859-1"
        lowerCaseHeaders = self.getLowerCaseHeaders()
        if not 'content-type' in lowerCaseHeaders:
            #hmmm... wtf?!
            self._body = body
        else:
            if not re.findall('text/(\w+)', lowerCaseHeaders['content-type'] ):
                # Not text, save as it is.
                self._body = body
            else:
                # According to the web server, the body content is a text/html content
                
                # I'll get the charset from the response headers, and the charset from the HTML content meta tag
                # if the charsets differ, then I'll decode the text with one encoder, and then with the other; comparing
                # which of the two generated less encoding errors. The one with less encoding errors is going to be
                # set as the self._body variable.
                
                # Go for the headers
                headers_charset = ''
                reCharset = re.findall('charset=([\w-]+)', lowerCaseHeaders['content-type'] )
                if reCharset:
                    # well... it seems that they are defining a charset in the response headers..
                    headers_charset = reCharset[0].lower()
                    
                # Now go for the meta tag
                # I parse <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> ?
                meta_charset = ''
                reCharset = re.findall('<meta.*?content=".*?charset=([\w-]+)".*?>', body, re.IGNORECASE )
                if reCharset:
                    # well... it seems that they are defining a charset in meta tag...
                    meta_charset = reCharset[0].lower()
                
                # by default we asume:
                charset = 'utf-8'
                if meta_charset == '' and headers_charset != '':
                    charset = headers_charset
                elif headers_charset == '' and meta_charset != '':
                    charset = meta_charset
                elif headers_charset == meta_charset:
                    charset = headers_charset
                elif meta_charset != headers_charset:
                    om.out.debug('The remote web application sent charset="'+ headers_charset + '" in the header, but charset="' +\
                    meta_charset +'" in the HTML body meta tag.')
                    
                    # decode the body with the headers_charset
                    decoded_with_headers = body.decode(headers_charset, 'returnStringToIdentifyError')
                    errors_decoding_with_headers = decoded_with_headers.count(STRING_TO_IDENTIFY_ERRORS)
                    
                    # decode the body with the meta_charset
                    decoded_with_meta = body.decode(meta_charset, 'returnStringToIdentifyError')
                    errors_decoding_with_meta = decoded_with_meta.count(STRING_TO_IDENTIFY_ERRORS)
                    
                    if errors_decoding_with_headers >= errors_decoding_with_meta:
                        charset = meta_charset
                    else:
                        charset = headers_charset
                    
                # Now that we have the charset, we use it!
                # The return value of the decode function is a unicode string.
                self._body = body.decode(charset, 'returnEscapedChar')

    def setHeaders( self, headers ): self._headers = headers
    def setURL( self, url ): self._realurl = url
    def setURI( self, uri ): self._uri = uri
    def setWaitTime( self, t ): self._time = t

    def __repr__( self ):
        return '< httpResponse | ' + str(self.getCode()) + ' | ' + self.getURL() + ' >'
    
    def dumpResponseHead( self ):
        '''
        @return: A string with:
            HTTP/1.1 /login.html 200
            Header1: Value1
            Header2: Value2
        '''
        strRes = 'HTTP/1.1 ' + str(self._code) + ' ' + self._msg + '\n'
        strRes += self.dumpHeaders()
        return strRes
        
    def dump( self ):
        '''
        Return a DETAILED str representation of this HTTP response object.
        '''
        strRes = self.dumpResponseHead()
        strRes += '\n\n'
        strRes += self._body
        return strRes
        
    def dumpHeaders( self ):
        '''
        @return: a str representation of the headers.
        '''
        strRes = ''
        for header in self._headers:
            strRes += header + ': ' + self._headers[ header ] + '\n'
        return strRes
        
