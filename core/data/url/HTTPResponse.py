'''
HTTPResponse.py

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
from itertools import imap

import core.controllers.outputManager as om

from core.data.misc.encoding import smart_unicode, ESCAPED_CHAR
from core.data.constants.encodings import DEFAULT_ENCODING
from core.data.parsers.url import URL
from core.data.dc.headers import Headers

DEFAULT_CHARSET = DEFAULT_ENCODING
CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '

CHARSET_EXTRACT_RE = re.compile('charset=\s*?([\w-]+)')
CHARSET_META_RE = re.compile('<meta.*?content=".*?charset=\s*?([\w-]+)".*?>')


def from_httplib_resp(httplibresp, original_url=None):
    '''
    Factory function. Build a HTTPResponse object from a httplib.HTTPResponse
    instance
    
    @param httplibresp: httplib.HTTPResponse instance
    @param original_url: Optional 'url_object' instance.
    
    @return: A HTTPResponse instance
    '''
    resp = httplibresp
    code, msg, hdrs, body = (resp.code, resp.msg, resp.info(), resp.read())
    hdrs = Headers(hdrs.items())
    
    if original_url:
        url_inst = URL(resp.geturl(), original_url.encoding)
        url_inst = url_inst.urlDecode()
    else:
        url_inst = original_url = URL(resp.geturl())
    
    charset = getattr(resp, 'encoding', None)
    return HTTPResponse(code, body, hdrs, url_inst,
                        original_url, msg, charset=charset)


class HTTPResponse(object):
    
    DOC_TYPE_TEXT_OR_HTML = 'DOC_TYPE_TEXT_OR_HTML'
    DOC_TYPE_SWF = 'DOC_TYPE_SWF'
    DOC_TYPE_PDF = 'DOC_TYPE_PDF'
    DOC_TYPE_IMAGE = 'DOC_TYPE_IMAGE'
    DOC_TYPE_OTHER = 'DOC_TYPE_OTHER'

    def __init__(self, code, read, headers, geturl, original_url,
                 msg='OK', _id=None, time=0.2, alias=None, charset=None):
        '''
        @param code: HTTP code
        @param read: HTTP body text; typically a string
        @param headers: HTTP headers, typically a dict or a httplib.HTTPMessage
        @param geturl: URL object instance
        @param original_url: URL object instance
        @param msg: HTTP message
        @param id: Optional response identifier
        @param time: The time between the request and the response
        @param alias: Optional alias for the response
        @param charset: Response's encoding; obligatory when `read` is unicode
        '''
        if not isinstance(geturl, URL):
            raise TypeError('Invalid type %s for HTTPResponse ctor param geturl.'
                            % type(geturl))

        if not isinstance(original_url, URL):
            raise TypeError('Invalid type %s for HTTPResponse ctor param original_url.'
                            % type(original_url))

        if not isinstance(headers, Headers):
            raise TypeError('Invalid type %s for HTTPResponse ctor param headers.' 
                            % type(headers))
        
        self._charset = charset
        self._headers = None
        self._body = None
        self._raw_body = read
        self._content_type = None
        self._dom = None
        self._clear_text_body = None
        # A unique id identifier for the response
        self.id = _id
        # From cache defaults to False
        self._fromCache = False
        # Set the info
        self._info = headers
        # Set code
        self.setCode(code)
        
        # Set the URL variables
        # The URL that we really GET'ed
        self._realurl = original_url.uri2url()
        self._uri = original_url
        # The URL where we were redirected to (equal to original_url
        # when no redirect)
        self._redirectedURL = geturl
        self._redirectedURI = geturl.uri2url()

        # Set the rest
        self._msg = msg
        self._time = time
        self._alias = alias
        self._doc_type = None
    
    def __contains__(self, string_to_test):
        '''
        Determine if the `string_to_test` is contained by the HTTP response
        body.

        @param string_to_test: String to look for in the body  
        '''
        return string_to_test in self.body
    
    def __repr__(self):

        vals = {
            'code': self.getCode(),
            'url': str(self.getURL()),
            'id': self.id and ' | id:%s' % self.id or '',
            'fcache': self._fromCache and ' | fromCache:True' or ''
            }
        return '<HTTPResponse | %(code)s | %(url)s%(id)s%(fcache)s>' % vals
    
    def set_id(self, id):
        self.id = id
    
    def getId(self):
        return self.id

    def setCode(self, code):
        self._code = code
    
    def getCode(self):
        return self._code

    @property
    def body(self):
        if self._body is None:
            self._body, self._charset = self._charset_handling()
            # Free 'raw_body'
            self._raw_body = None
        return self._body
    
    @body.setter
    def body(self, body):
        # Reset body
        self._body = None
        self._raw_body = body
    
    def setBody(self, body):
        '''
        Setter for body.

        @body: A string that represents the body of the HTTP response
        '''
        self.body = body
    
    def getBody(self):
        return self.body

    def getClearTextBody(self):
        '''
        @return: A clear text representation of the HTTP response body. 
        '''
        
        clear_text_body = self._clear_text_body
        
        if clear_text_body is None:
            # Calculate the clear text body
            dom = self.getDOM()
            if dom is not None:
                clear_text_body = self._clear_text_body = ''.join(dom.itertext())
        
        return clear_text_body

    def setDOM(self, dom_inst):
        '''
        This setter is part of a performance improvement I'm talking about in
        getDOM() and sgmlParser._parse().
        
        Without this setDOM() which is called from sgmlParser._parse() when the
        code runs:
            sgmlParser( http_response )
            ...
            http_response.getDOM()
        
        The DOM is calculated twice.
        
        We still need to figure out how to solve the other issue which should
        aim to avoid the double DOM generation when:
            http_response.getDOM()
            ...
            sgmlParser( http_response )
        
        @return: None
        '''
        self._dom = dom_inst

    def getDOM(self):
        '''
        I don't want to calculate the DOM for all responses, only for those
        which are needed. This method will first calculate the DOM, and then
        save it for upcoming calls.
        
        @see: TODO: Potential performance improvement in sgmlParser._parse()
                    for ideas on how to reduce CPU usage.
                            
        @return: The DOM, or None if the HTML normalization failed.
        '''
        if self._dom is None:
            try:
                parser = etree.HTMLParser(recover=True)
                self._dom = etree.fromstring(self.body, parser)
            except Exception:
                msg = ('The HTTP body for "%s" could NOT be parsed by lxml.'
                       % self.getURL())
                om.out.debug(msg)
        return self._dom
    
    @property
    def charset(self):
        if not self._charset:
            self._body, self._charset = self._charset_handling()
            # Free 'raw_body'
            self._raw_body = None
        return self._charset
    
    @charset.setter
    def charset(self, charset):
        self._charset = charset
    
    def setCharset(self, charset):
        self.charset = charset
    
    def getCharset(self):
        return self.charset
    
    def setRedirURL(self, ru):
        self._redirectedURL = ru
    
    def getRedirURL(self):
        return self._redirectedURL

    def setRedirURI(self, ru):
        self._redirectedURI = ru
    
    def getRedirURI(self):
        return self._redirectedURI

    @property
    def headers(self):
        if self._headers is None:
            self.headers = self._info
            assert self._headers is not None
        return self._headers
    
    @headers.setter
    def headers(self, headers):
        # Fix lowercase in header names from HTTPMessage
        if isinstance(headers, httplib.HTTPMessage):
            self._headers = Headers()
            for header in headers.headers:
                key, value = header.split(':', 1)
                self._headers[key.strip()] = value.strip()
        else:
            self._headers = headers

        # Set the type, for easy access.
        self._doc_type = HTTPResponse.DOC_TYPE_OTHER
        find_word = lambda w: content_type.find(w) != -1
        
        content_type_hvalue, _ = self._headers.iget('content-type', None)
        
        # we need exactly content type but not charset
        if content_type_hvalue is not None:
            try:
                self._content_type = content_type_hvalue.split(';', 1)[0]
            except:
                msg = 'Invalid Content-Type value "%s" sent in HTTP response.'
                om.out.debug(msg % (content_type_hvalue,))
            else:
                content_type = self._content_type.lower()
        
                # Set the doc_type
                if content_type.count('image'):
                    self._doc_type = HTTPResponse.DOC_TYPE_IMAGE
                
                elif content_type.count('pdf'):
                    self._doc_type = HTTPResponse.DOC_TYPE_PDF
                
                elif content_type.count('x-shockwave-flash'):
                    self._doc_type = HTTPResponse.DOC_TYPE_SWF
                
                elif any(imap(find_word,
                              ('text', 'html', 'xml', 'txt', 'javascript'))):
                    self._doc_type = HTTPResponse.DOC_TYPE_TEXT_OR_HTML

    def setHeaders(self, headers):
        '''
        Sets the headers and also analyzes them in order to get the response
        mime type (text/html , application/pdf, etc).

        @param headers: The headers dict.
        '''
        self.headers = headers
    
    def getHeaders(self):
        return self.headers

    def getLowerCaseHeaders(self):
        '''
        If the original headers were:
            {'Abc-Def': 'F00N3s'}
        This will return:
            {'abc-def': 'F00N3s'}
        
        The only thing that changes is the header name.
        '''
        lcase_headers = dict((k.lower(), v) for k, v in self.headers.iteritems())
        return Headers(lcase_headers.items())

    def setURL(self, url):
        '''
        >>> url = URL('http://www.google.com')
        >>> r = HTTPResponse(200, '' , Headers(), url, url)
        >>> r.setURL('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The URL of a HTTPResponse object must be of url.URL type.
        >>> r.setURL(url)
        >>> r.getURL() == url
        True
        '''
        if not isinstance(url, URL):
            raise TypeError('The URL of a HTTPResponse object must be of '
                             'url.URL type.')
        
        self._realurl = url.uri2url()
        
    def getURL(self):
        return self._realurl

    def setURI(self, uri):
        '''
        >>> uri = URL('http://www.google.com/')
        >>> r = HTTPResponse(200, '' , Headers(), uri, uri)
        >>> r.setURI('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The URI of a HTTPResponse object must be of url.URL type.
        >>> r.setURI(uri)
        >>> r.getURI() == uri
        True
        
        '''
        if not isinstance(uri, URL):
            raise TypeError('The URI of a HTTPResponse object must be of '
                             'url.URL type.')
        
        self._uri = uri
        self._realurl = uri.uri2url()

    def getURI(self):
        return self._uri

    def was_redirected(self):
        return self._uri != self._redirectedURI

    def set_from_cache(self, fcache):
        '''
        @param fcache: True if this response was obtained from the
        local cache.
        '''
        self._fromCache = fcache
    
    def getFromCache(self):
        '''
        @return: True if this response was obtained from the local cache.
        '''
        return self._fromCache

    def set_wait_time(self, t):
        self._time = t
    
    def getWaitTime(self):
        return self._time

    def setAlias(self, alias):
        self._alias = alias
        
    def getAlias(self):
        return self._alias

    def info(self):
        return self._info

    def getStatusLine(self):
        '''Return status-line of response.'''
        return 'HTTP/1.1' + SP + str(self._code) + SP + self._msg + CRLF
    
    def getMsg(self):
        return self._msg
    
    def _charset_handling(self):
        '''
        Decode the body based on the header (or metadata) encoding.
        The implemented algorithm follows the encoding detection logic
        used by FF:

            1) First try to find a charset using the following search criteria:
                a) Look in the 'content-type' HTTP header. Example:
                    content-type: text/html; charset=iso-8859-1
                b) Look in the 'meta' HTML header. Example:
                    <meta .* content="text/html; charset=utf-8" />
                c) Determine the charset using the chardet module (TODO)
                d) Use the DEFAULT_CHARSET
            
            2) Try to decode the body using the found charset. If it fails,
            then force it to use the DEFAULT_CHARSET
        
        Finally return the unicode (decoded) body and the used charset.  
        
        Note: If the body is already a unicode string return it as it is.
        '''
        lcase_headers = self.getLowerCaseHeaders()
        charset = self._charset
        rawbody = self._raw_body
        
        # Only try to decode <str> strings. Skip <unicode> strings
        if type(rawbody) is unicode:
            _body = rawbody
            assert charset is not None, ("HTTPResponse objects containing "
                             "unicode body must have an associated charset")
        elif 'content-type' not in lcase_headers:
            _body = rawbody
            charset = DEFAULT_CHARSET

            if self._code not in (301, 302, 401):
                msg = "The remote web server failed to send the 'content-type'"\
                      " header in HTTP response with id %s" % self.id
                om.out.debug(msg)
                
        elif not self.is_text_or_html():
            # Not text, save as it is.
            _body = rawbody
            charset = charset or DEFAULT_CHARSET
        else:
            # Figure out charset to work with
            if not charset:
                # Start with the headers
                charset_mo = CHARSET_EXTRACT_RE.search(
                                                lcase_headers['content-type'],
                                                re.I)
                if charset_mo:
                    # Seems like the response's headers contain a charset
                    charset = charset_mo.groups()[0].lower().strip()
                else:
                    # Continue with the body's meta tag
                    charset_mo = CHARSET_META_RE.search(rawbody, re.IGNORECASE)
                    if charset_mo:
                        charset = charset_mo.groups()[0].lower().strip()
                    else:
                        charset = DEFAULT_CHARSET

            # Now that we have the charset, we use it!
            # The return value of the decode function is a unicode string.
            try:
                _body = smart_unicode(
                                rawbody,
                                charset,
                                errors=ESCAPED_CHAR,
                                on_error_guess=False
                            )
            except LookupError:
                # Warn about a buggy charset
                msg = ('Charset LookupError: unknown charset: %s; '
                    'ignored and set to default: %s' % 
                    (charset, self._charset))
                om.out.debug(msg)
                # Forcing it to use the default
                charset = DEFAULT_CHARSET
                _body = smart_unicode(
                                rawbody,
                                charset,
                                errors=ESCAPED_CHAR,
                                on_error_guess=False
                            )
            
        return _body, charset
    
    @property
    def content_type(self):
        '''
        The content type of the response
        '''
        if self._content_type is None:
            self.headers = self._info
        return self._content_type or ''

    @property
    def doc_type(self):
        if self._doc_type is None:
            self.headers = self._info
            assert self._doc_type is not None
        return self._doc_type

    def is_text_or_html(self):
        '''
        @return: True if this response is text or html
        '''
        return self.doc_type == HTTPResponse.DOC_TYPE_TEXT_OR_HTML
    
    def is_pdf(self):
        '''
        @return: True if this response is a PDF file
        '''
        return self.doc_type == HTTPResponse.DOC_TYPE_PDF
    
    def is_swf(self):
        '''
        @return: True if this response is a SWF file
        '''
        return self.doc_type == HTTPResponse.DOC_TYPE_SWF

    def is_image(self):
        '''
        @return: True if this response is an image file
        '''
        return self.doc_type == HTTPResponse.DOC_TYPE_IMAGE
    
    def dumpResponseHead(self):
        '''
        @return: A string with:
            HTTP/1.1 /login.html 200
            Header1: Value1
            Header2: Value2
        '''
        dump_head = "%s%s" % (self.getStatusLine(), self.dumpHeaders())
        if type(dump_head) is unicode:
            dump_head = dump_head.encode(self.charset)
        return dump_head

    def dump(self):
        '''
        Return a DETAILED str representation of this HTTP response object.
        '''
        body = self.body
        # Images, pdf and binary responses in general are never decoded
        # to unicode
        if isinstance(body, unicode):
            body = body.encode(DEFAULT_CHARSET, 'replace')
        return "%s%s%s" % (self.dumpResponseHead(), CRLF, body)
        
    def dumpHeaders(self):
        '''
        @return: a str representation of the headers.
        '''
        if self.headers:
            return CRLF.join(h + ': ' + hv  for h, hv in self.headers.items()) + CRLF
        else:
            return ''
        
    def copy(self):
        return copy.deepcopy(self)