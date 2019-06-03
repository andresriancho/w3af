"""
HTTPResponse.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import re
import zlib
import copy
import httplib
import urllib2
import threading
from itertools import imap

import w3af.core.controllers.output_manager as om
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.misc.encoding import smart_unicode, smart_str_ignore, ESCAPED_CHAR
from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.db.disk_item import DiskItem


DEFAULT_CHARSET = DEFAULT_ENCODING
CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '

CONTENT_TYPE = 'content-type'
STATUS_LINE = 'HTTP/1.1 %s %s' + CRLF

CHARSET_EXTRACT_RE = re.compile('charset=\s*?([\w-]+)')
CHARSET_META_RE = re.compile('<meta.*?content=".*?charset=\s*?([\w-]+)".*?>')
DEFAULT_WAIT_TIME = 0.2


class HTTPResponse(DiskItem):

    DOC_TYPE_TEXT_OR_HTML = 'DOC_TYPE_TEXT_OR_HTML'
    DOC_TYPE_SWF = 'DOC_TYPE_SWF'
    DOC_TYPE_PDF = 'DOC_TYPE_PDF'
    DOC_TYPE_IMAGE = 'DOC_TYPE_IMAGE'
    DOC_TYPE_OTHER = 'DOC_TYPE_OTHER'

    __slots__ = ('_code',
                 '_charset',
                 '_headers',
                 '_body',
                 '_raw_body',
                 '_binary_response',
                 '_content_type',
                 '_dom',
                 'id',
                 '_from_cache',
                 '_info',
                 '_realurl',
                 '_uri',
                 '_redirected_url',
                 '_redirected_uri',
                 '_msg',
                 '_time',
                 '_alias',
                 '_doc_type',
                 '_body_lock',
                 '_debugging_id')

    def __init__(self, code, read, headers, geturl, original_url,
                 msg='OK', _id=None, time=DEFAULT_WAIT_TIME, alias=None,
                 charset=None, binary_response=False, set_body=False,
                 debugging_id=None):
        """
        :param code: HTTP code
        :param read: HTTP body text; typically a string
        :param headers: HTTP headers, typically a dict or a httplib.HTTPMessage
        :param geturl: URL object instance
        :param original_url: URL object instance
        :param msg: HTTP message
        :param _id: Optional response identifier
        :param time: The time between the request and the response
        :param alias: Alias for the response, this contains a hash that helps
                      the backend sqlite find http_responses faster by indexing
                      by this attr.
        :param charset: Response's encoding; obligatory when `read` is unicode
        """
        if not isinstance(geturl, URL):
            msg = 'Invalid type %s for HTTPResponse ctor param geturl.'
            raise TypeError(msg % type(geturl))

        if not isinstance(original_url, URL):
            msg = 'Invalid type %s for HTTPResponse ctor param original_url.'
            raise TypeError(msg % type(original_url))

        if not isinstance(headers, Headers):
            msg = 'Invalid type %s for HTTPResponse ctor param headers.'
            raise TypeError(msg % type(headers))
        
        if not isinstance(read, basestring):
            raise TypeError('Invalid type %s for HTTPResponse ctor param read.'
                            % type(read))

        self._charset = charset
        self._headers = None

        if set_body and isinstance(read, unicode):
            # We use this case for deserialization via from_dict()
            #
            # The goal is to prevent the body to be analyzed for charset data
            # once again, since it was already done during to_dict() in the
            # get_body() call.
            self._body = self._raw_body = read
        else:
            self._body = None
            self._raw_body = read

        self._binary_response = binary_response
        self._content_type = None
        self._dom = None
        # A unique id identifier for the response
        self.id = _id
        # From cache defaults to False
        self._from_cache = False
        # Set the info
        self._info = headers
        # Set code
        self._code = None
        self.set_code(code)

        # Set the URL variables
        # The URL that we really GET'ed
        self._realurl = original_url.uri2url()
        self._uri = original_url
        # The URL where we were redirected to (equal to original_url
        # when no redirect)
        self._redirected_url = geturl.uri2url()
        self._redirected_uri = geturl

        # Set the rest
        self._msg = smart_unicode(msg)
        self._time = time
        self._alias = alias
        self._doc_type = None
        self._debugging_id = debugging_id
        
        # Internal lock
        self._body_lock = threading.RLock()

    @classmethod
    def from_httplib_resp(cls, httplibresp, original_url=None, binary_response=False):
        """
        Factory function. Build a HTTPResponse object from a
        httplib.HTTPResponse instance
    
        :param httplibresp: httplib.HTTPResponse instance
        :param original_url: Optional 'url_object' instance.
    
        :return: A HTTPResponse instance
        """
        resp = httplibresp
        code, msg, hdrs, body = (resp.code, resp.msg, resp.info(), resp.read())
        hdrs = Headers(hdrs.items())

        if original_url:
            url_inst = URL(resp.geturl(), original_url.encoding)
            url_inst = url_inst.url_decode()
        else:
            url_inst = original_url = URL(resp.geturl())

        httplib_time = DEFAULT_WAIT_TIME
        if hasattr(httplibresp, 'get_wait_time'):
            # This is defined in the keep alive http response object
            httplib_time = httplibresp.get_wait_time()

        if isinstance(resp, urllib2.HTTPError):
            # This is possible because in errors.py I do:
            # err = urllib2.HTTPError(req.get_full_url(), code, msg, hdrs, resp)
            charset = getattr(resp.fp, 'encoding', None)
        else:
            # The encoding attribute is only set on CachedResponse instances
            charset = getattr(resp, 'encoding', None)
        
        return cls(code, body, hdrs, url_inst, original_url,
                   msg, charset=charset, time=httplib_time,
                   binary_response=binary_response)

    @classmethod
    def from_dict(cls, unserialized_dict):
        """
        * msgpack is MUCH faster than cPickle,
        * msgpack can't serialize python objects,
        * I have to create a dict representation of HTTPResponse to serialize it
        * and a from_dict to have the object back
        
        :param unserialized_dict: A dict just as returned by to_dict()
        """
        code = unserialized_dict['code']
        msg = unserialized_dict['msg']
        headers = unserialized_dict['headers']
        body = unserialized_dict['body']
        charset = unserialized_dict['charset']
        _time = unserialized_dict['time']
        _id = unserialized_dict['id']
        url = URL(unserialized_dict['uri'])
        debugging_id = unserialized_dict['debugging_id']

        headers_inst = Headers(headers.items())

        return cls(code, body, headers_inst, url, url,
                   msg=msg,
                   _id=_id,
                   time=_time,
                   charset=charset,
                   set_body=True,
                   debugging_id=debugging_id)

    def to_dict(self):
        """
        :return: A dict that represents the current object and is serializable
                 by the json or msgpack modules.
        """
        # Note: The Headers() object can be serialized by msgpack because it
        #       inherits from dict() and doesn't mangle it too much
        return {'headers': dict(self.get_headers()),
                'code': self.get_code(),
                'msg': self.get_msg(),
                'body': self.get_body(),
                'time': self.get_wait_time(),
                'id': self.get_id(),
                'charset': self.get_charset(),
                'uri': self.get_uri().url_string,
                'debugging_id': self._debugging_id}

    def get_eq_attrs(self):
        return ('_code',
                '_charset',
                '_headers',
                '_body',
                '_raw_body',
                '_binary_response',
                '_content_type',
                'id',
                '_from_cache',
                '_info',
                '_realurl',
                '_uri',
                '_redirected_url',
                '_redirected_uri',
                '_msg',
                '_time',
                '_alias',
                '_doc_type',
                '_debugging_id')

    def __contains__(self, string_to_test):
        """
        Determine if the `string_to_test` is contained by the HTTP response
        body.

        :param string_to_test: String to look for in the body
        """
        return string_to_test in self.body
    
    def __eq__(self, other):
        return (self.id == other.id and
                self._code == other._code and
                self.headers == other.headers and
                self.body == other.body and
                self._uri == other._uri)

    def __repr__(self):
        vals = {
            'code': self.get_code(),
            'url': str(self.get_url()),
            'id': self.id and ' | id:%s' % self.id or '',
            'fcache': self._from_cache and ' | fcache:True' or ''
        }
        return '<HTTPResponse | %(code)s | %(url)s%(id)s%(fcache)s>' % vals

    def set_id(self, _id):
        self.id = _id

    def get_id(self):
        return self.id

    def set_debugging_id(self, debugging_id):
        self._debugging_id = debugging_id

    def get_debugging_id(self):
        return self._debugging_id

    def set_code(self, code):
        self._code = code

    def get_code(self):
        return self._code

    @staticmethod
    def _quick_hash(text):
        return '%s%s' % (hash(text), zlib.adler32(text))

    def get_body_hash(self):
        body = smart_str_ignore(self.get_body())
        return self._quick_hash(body)

    def get_hash(self, exclude_headers=None):
        exclude_headers = [] or exclude_headers

        headers = self.dump_response_head(exclude_headers=exclude_headers)
        body = smart_str_ignore(self.get_body())

        args = (headers, body)
        dump = '%s%s' % args

        return self._quick_hash(dump)

    def get_body(self):
        if self._body is not None:
            return self._body

        with self._body_lock:
            self._body, self._charset = self._charset_handling()

            # The user wants the raw body, without any modifications / decoding?
            if not self._binary_response:
                self._raw_body = None

            return self._body

    def set_body(self, body):
        """
        Setter for body.

        @body: A string that represents the body of the HTTP response
        """
        if not isinstance(body, basestring):
            msg = 'Invalid type %s for set_body parameter body.'
            raise TypeError(msg % type(body))
            
        self._body = None
        self._raw_body = body

    body = property(get_body, set_body)

    def get_raw_body(self):
        """
        Return the raw body as it came from the wire.

        This is useful when we want to parse binary files such as images and DS_Store.

        IMPORTANT! Because we want to save some memory the raw body will be set
                   to None after the first call to get_body(), so please use
                   binary_response in your requests in order to let us know
                   that you want the raw body

        :return: The raw body as it came from the wire
        """
        return self._raw_body

    def get_clear_text_body(self):
        """
        Just a shortcut to get the clear text body
        :return: A unicode string
        """
        parser = self.get_parser()
        if parser is not None:
            return parser.get_clear_text_body()

        return u''

    def get_parser(self):
        """
        Just a shortcut to get the parser for this response, we get this from
        the document parser cache.

        :return: A DocumentParser instance or None
        """
        try:
            return parser_cache.dpc.get_document_parser_for(self)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return

    def get_charset(self):
        if self._charset:
            return self._charset

        with self._body_lock:
            self._body, self._charset = self._charset_handling()

            # The user wants the raw body, without any modifications / decoding?
            if not self._binary_response:
                self._raw_body = None

        return self._charset

    def set_charset(self, charset):
        self._charset = charset
    
    charset = property(get_charset, set_charset)
    
    def set_redir_url(self, ru):
        self._redirected_url = ru

    def get_redir_url(self):
        return self._redirected_url

    def set_redir_uri(self, ru):
        self._redirected_uri = ru

    def get_redir_uri(self):
        return self._redirected_uri

    def get_headers(self):
        if self._headers is None:
            self.headers = self._info
            assert self._headers is not None
        return self._headers

    def set_headers(self, headers):
        """
        Sets the headers and also analyzes them in order to get the response
        mime type (text/html , application/pdf, etc).

        :param headers: The headers dict.
        """
        # Fix lowercase in header names from HTTPMessage
        if isinstance(headers, httplib.HTTPMessage):
            self._headers = Headers()
            for header in headers.headers:
                key, value = header.split(':', 1)
                self._headers[key.strip()] = value.strip()
        else:
            self._headers = headers

        find_word = lambda w: content_type.find(w) != -1

        content_type_hvalue, _ = self._headers.iget(CONTENT_TYPE, None)

        # we need exactly content type but not charset
        if content_type_hvalue is not None:
            try:
                self._content_type = content_type_hvalue.split(';', 1)[0].strip().lower()
            except:
                msg = 'Invalid Content-Type value "%s" sent in HTTP response.'
                om.out.debug(msg % (content_type_hvalue,))
            else:
                content_type = self._content_type

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

        # Check if the doc type is still None, that would mean that none of the
        # previous if statements matched.
        #
        # Note that I'm doing this here and not before the other if statements
        # because that triggered a race condition with threads asking if the
        # _doc_type was != None (which it was because I was setting it to
        # DOC_TYPE_OTHER) and that raised all types of errors.
        if self._doc_type is None:
            self._doc_type = HTTPResponse.DOC_TYPE_OTHER

    headers = property(get_headers, set_headers)

    def get_lower_case_headers(self):
        """
        If the original headers were:
            {'Abc-Def': 'F00N3s'}
        This will return:
            {'abc-def': 'F00N3s'}

        The only thing that changes is the header name.
        """
        return Headers([(k.lower(), v) for k, v in self.headers.iteritems()])

    def set_url(self, url):
        """
        >>> url = URL('http://www.google.com')
        >>> r = HTTPResponse(200, '' , Headers(), url, url)
        >>> r.set_url('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The URL of a HTTPResponse object must be of url.URL type.
        >>> r.set_url(url)
        >>> r.get_url() == url
        True
        """
        if not isinstance(url, URL):
            raise TypeError('The URL of a HTTPResponse object must be of '
                            'url.URL type.')

        self._realurl = url.uri2url()

    def get_url(self):
        return self._realurl

    def get_host(self):
        return self.get_url().get_domain()

    def set_uri(self, uri):
        """
        >>> uri = URL('http://www.google.com/')
        >>> r = HTTPResponse(200, '' , Headers(), uri, uri)
        >>> r.set_uri('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The URI of a HTTPResponse object must be of url.URL type.
        >>> r.set_uri(uri)
        >>> r.get_uri() == uri
        True

        """
        if not isinstance(uri, URL):
            raise TypeError('The URI of a HTTPResponse object must be of '
                            'url.URL type.')

        self._uri = uri
        self._realurl = uri.uri2url()

    def get_uri(self):
        return self._uri

    def was_redirected(self):
        return self._uri != self._redirected_uri

    def set_from_cache(self, fcache):
        """
        :param fcache: True if this response was obtained from the
        local cache.
        """
        self._from_cache = fcache

    def get_from_cache(self):
        """
        :return: True if this response was obtained from the local cache.
        """
        return self._from_cache

    def set_wait_time(self, t):
        self._time = t

    def get_wait_time(self):
        return self._time

    def set_alias(self, alias):
        self._alias = alias

    def get_alias(self):
        return self._alias

    def info(self):
        return self._info

    def get_status_line(self):
        """
        Return status-line of response.
        """
        return STATUS_LINE % (self._code, self._msg)

    def get_msg(self):
        return self._msg

    def _charset_handling(self):
        """
        Decode the body based on the header (or metadata) encoding.
        The implemented algorithm follows the encoding detection logic
        used by FF:

            1) First try to find a charset using the following search criteria:
                a) Look in the CONTENT_TYPE HTTP header. Example:
                    content-type: text/html; charset=iso-8859-1
                b) Look in the 'meta' HTML header. Example:
                    <meta .* content="text/html; charset=utf-8" />
                c) Determine the charset using the chardet module (TODO)
                d) Use the DEFAULT_CHARSET

            2) Try to decode the body using the found charset. If it fails,
            then force it to use the DEFAULT_CHARSET

        Finally return the unicode (decoded) body and the used charset.

        Note: If the body is already a unicode string return it as it is.
        """
        charset = self._charset
        raw_body = self._raw_body
        headers = self.get_headers()
        content_type, _ = headers.iget(CONTENT_TYPE, None)

        # Only try to decode <str> strings. Skip <unicode> strings
        if type(raw_body) is unicode:
            _body = raw_body
            assert charset is not None, ("HTTPResponse objects containing "
                                         "unicode body must have an associated "
                                         "charset")
        elif content_type is None:
            _body = raw_body
            charset = DEFAULT_CHARSET

            if _body:
                msg = ('The remote web server failed to send the CONTENT_TYPE'
                       ' header in HTTP response with id %s')
                om.out.debug(msg % self.id)

        elif not self.is_text_or_html():
            # Not text, save as it is.
            _body = raw_body
            charset = charset or DEFAULT_CHARSET
        else:
            # Figure out charset to work with
            if not charset:
                charset = self.guess_charset(raw_body, headers)

            # Now that we have the charset, we use it!
            # The return value of the decode function is a unicode string.
            try:
                _body = smart_unicode(raw_body,
                                      charset,
                                      errors=ESCAPED_CHAR,
                                      on_error_guess=False)
            except LookupError:
                # Warn about a buggy charset
                msg = ('Charset LookupError: unknown charset: %s; '
                       'ignored and set to default: %s' %
                       (charset, DEFAULT_CHARSET))
                om.out.debug(msg)

                # Forcing it to use the default
                charset = DEFAULT_CHARSET
                _body = smart_unicode(raw_body,
                                      charset,
                                      errors=ESCAPED_CHAR,
                                      on_error_guess=False)

        return _body, charset

    def guess_charset(self, raw_body, headers):
        # Start with the headers
        content_type, _ = headers.iget(CONTENT_TYPE, None)
        charset_mo = CHARSET_EXTRACT_RE.search(content_type, re.I)
        if charset_mo:
            # Seems like the response's headers contain a charset
            charset = charset_mo.groups()[0].lower().strip()
        else:
            # Continue with the body's meta tag
            charset_mo = CHARSET_META_RE.search(raw_body, re.IGNORECASE)
            if charset_mo:
                charset = charset_mo.groups()[0].lower().strip()
            else:
                charset = DEFAULT_CHARSET

        return charset

    @property
    def content_type(self):
        """
        The content type of the response
        """
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
        """
        :return: True if this response is text or html
        """
        return self.doc_type == HTTPResponse.DOC_TYPE_TEXT_OR_HTML

    def is_pdf(self):
        """
        :return: True if this response is a PDF file
        """
        return self.doc_type == HTTPResponse.DOC_TYPE_PDF

    def is_swf(self):
        """
        :return: True if this response is a SWF file
        """
        return self.doc_type == HTTPResponse.DOC_TYPE_SWF

    def is_image(self):
        """
        :return: True if this response is an image file
        """
        return self.doc_type == HTTPResponse.DOC_TYPE_IMAGE

    def dump_response_head(self, exclude_headers=None):
        """
        :return: A byte-string, as we would send to the wire, containing:

            HTTP/1.1 /login.html 200
            Header1: Value1
            Header2: Value2

        """
        exclude_headers = exclude_headers or []
        status_line = self.get_status_line()
        dumped_headers = self.dump_headers(exclude_headers=exclude_headers)

        dump_head = '%s%s' % (status_line, dumped_headers)

        if isinstance(dump_head, unicode):
            dump_head = dump_head.encode(self.charset, 'replace')

        return dump_head

    def dump(self):
        """
        Return a DETAILED str representation of this HTTP response object.
        """
        body = self.body

        # Images, pdf and binary responses in general are never decoded
        # to unicode
        if isinstance(body, unicode):
            body = body.encode(self.charset, 'replace')

        return '%s%s%s' % (self.dump_response_head(), CRLF, body)

    def dump_headers(self, exclude_headers=None):
        """
        :return: a str representation of the headers.
        """
        exclude_headers = exclude_headers or []

        if self.headers:
            return CRLF.join('%s: %s' % (h, hv) for
                             (h, hv) in self.headers.items()
                             if h.lower() not in exclude_headers) + CRLF
        else:
            return ''

    def get_redirect_destination(self):
        lower_headers = self.get_lower_case_headers()
        redirect_url = None

        for header_name in ('location', 'uri'):
            if header_name in lower_headers:
                header_value = lower_headers[header_name]
                header_value = header_value.strip()

                try:
                    redirect_url = self.get_url().url_join(header_value)
                except ValueError:
                    # No special invalid URL handling required
                    continue
                else:
                    break

        return redirect_url

    def does_redirect_outside_target(self):
        """
        :return: True when the redirect destination is not the same
                 domain and protocol than the originally requested URL
        """
        redirect_destination = self.get_redirect_destination()

        if redirect_destination is None:
            return False

        # Check if the protocol was changed:
        original_proto = self.get_url().get_protocol()
        redirect_proto = redirect_destination.get_protocol()

        if original_proto != redirect_proto:
            return True

        # Check if the domain was changed:
        original_domain = self.get_url().get_domain()
        redirect_domain = redirect_destination.get_domain()

        if original_domain != redirect_domain:
            return True

        return False

    def copy(self):
        return copy.deepcopy(self)

    def __getstate__(self):
        state = {k: getattr(self, k) for k in self.__slots__}
        state.pop('_body_lock')
        return state
    
    def __setstate__(self, state):
        [setattr(self, k, v) for k, v in state.iteritems()]
        self._body_lock = threading.RLock()
