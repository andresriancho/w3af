"""
fuzzable_request.py

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
import string
import base64

from itertools import chain
from urllib import unquote, quote, quote_plus

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.dc.generic.data_container import DataContainer
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.dc.factory import dc_from_hdrs_post
from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.request_mixin import RequestMixIn
from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.misc.encoding import smart_str_ignore


ALL_CHARS = ''.join(chr(i) for i in xrange(256))
TRANS_TABLE = string.maketrans(ALL_CHARS, ALL_CHARS)
DELETE_CHARS = ''.join(['\\',
                        "'",
                        '"',
                        '+',
                        ' ',
                        chr(0),
                        chr(int("0D", 16)),
                        chr(int("0A", 16))])


TYPE_ERROR = 'FuzzableRequest __init__ parameter %s needs to be of %s type'


class FuzzableRequest(RequestMixIn, DiskItem):
    """
    This class represents a fuzzable request. Fuzzable requests were created
    to allow w3af plugins to be much simpler and don't really care if the
    vulnerability is in the postdata, querystring, header, cookie or any other
    injection point.

    FuzzableRequest classes are just an easy to use representation of an HTTP
    Request, which will (during the audit phase) be wrapped into a Mutant
    and have its values modified.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # In most cases we don't care about these headers, even if provided by the
    # user, since they will be calculated based on the attributes we are
    # going to store and these won't be updated.
    REMOVE_HEADERS = ('content-length',)

    __slots__ = ('_method',
                 '_cookie',
                 '_post_data',
                 '_headers',
                 '_uri',
                 '_url',
                 '_sent_info_comp')

    def __init__(self, uri, method='GET', headers=None, cookie=None,
                 post_data=None):
        super(FuzzableRequest, self).__init__()

        # Note: Do not check for the URI/Headers type here, since I'm doing it
        # in set_uri() and set_headers() already.
        if cookie is not None and not isinstance(cookie, Cookie):
            raise TypeError(TYPE_ERROR % ('cookie', 'Cookie'))

        if post_data is not None and not isinstance(post_data, DataContainer):
            raise TypeError(TYPE_ERROR % ('post_data', 'DataContainer'))

        # Internal variables
        self._method = method
        self._cookie = Cookie() if cookie is None else cookie
        self._post_data = KeyValueContainer() if post_data is None else post_data

        # Set the headers
        self._headers = None
        pheaders = Headers() if headers is None else headers
        self.set_headers(pheaders)

        # Set the URL
        self._uri = None
        self._url = None
        self.set_uri(uri)

        # Set the internal variables
        self._sent_info_comp = None

    def __getstate__(self):
        state = {k: getattr(self, k) for k in self.__slots__}
        return state

    def __setstate__(self, state):
        [setattr(self, k, v) for k, v in state.iteritems()]

    def get_default_headers(self):
        """
        :return: The headers we want to use framework-wide for fuzzing. By
                 default we set the fuzzable_headers to [], which makes this
                 method return an empty Headers instance.

                 When the user sets a fuzzable_headers it will create a Headers
                 instance with empty values.

                 We then append the specific headers supplied for this
                 FuzzableRequest instance to the default headers. Any specific
                 headers override the default (empty) ones.
        """
        fuzzable_headers = cf.cf.get('fuzzable_headers') or []
        req_headers = [(h, '') for h in fuzzable_headers]
        return Headers(init_val=req_headers)

    @classmethod
    def from_parts(cls, url, method='GET', post_data=None, headers=None):
        """
        :return: An instance of FuzzableRequest from the provided parameters.
        """
        if isinstance(url, basestring):
            url = URL(url)

        if post_data == '':
            post_data = None

        elif isinstance(post_data, basestring):
            post_data = dc_from_hdrs_post(headers, post_data)

        return cls(url, method=method, headers=headers, post_data=post_data)

    @classmethod
    def from_http_response(cls, http_response):
        """
        :return: An instance of FuzzableRequest using the URL and cookie from
                 the http_response. The method used is "GET", and no post_data
                 is set.
        """
        cookie = Cookie.from_http_response(http_response)
        return cls(http_response.get_uri(), method='GET', cookie=cookie)

    @classmethod
    def from_http_request(cls, request):
        """
        :param request: The instance we'll use as base
        :return: An instance of FuzzableRequest based on a urllib2 HTTP request
                 instance.
        """
        headers = request.headers
        headers.update(request.unredirected_hdrs)
        headers = Headers(headers.items())

        post_data = request.get_data() or ''

        return cls.from_parts(request.url_object, method=request.get_method(),
                              headers=headers, post_data=post_data)

    @classmethod
    def from_form(cls, form, headers=None):
        if form.get_method().upper() == 'POST':
            r = cls(form.get_action(),
                    method=form.get_method(),
                    headers=headers,
                    post_data=form)
        else:
            # The default is a GET request
            form_action = form.get_action()
            form_action.querystring = form

            r = cls(form_action,
                    method=form.get_method(),
                    headers=headers)

        return r

    def to_base64(self):
        """
        :return: The whole HTTP request serialized and encoded as base64
        """
        raw_http_request = self.dump()
        return base64.b64encode(raw_http_request)

    @classmethod
    def from_base64(cls, base64_data):
        """
        :param base64_data: A string generated by to_base64
        :return: A FuzzableRequest instance
        """
        from w3af.core.data.parsers.doc.http_request_parser import raw_http_request_parser
        raw_http_request = base64.b64decode(base64_data)
        return raw_http_request_parser(raw_http_request)

    def make_comp(self, heterogen_string):
        """
        This basically removes characters that are used as escapes such as \
        """
        return string.translate(heterogen_string, TRANS_TABLE,
                                deletions=DELETE_CHARS)

    def sent(self, needle):
        """
        Checks if something similar to `needle` was sent in the request.
        This is used to remove false positives, e.g. if a grep plugin finds a
        "strange" string and wants to be sure it was not generated by an audit
        plugin.

        This method should only be used by grep plugins which often have false
        positives.

        The following example shows that we sent d'z"0 but d\'z"0 will
        as well be recognised as sent

        Note on performance:

            At some point I thought about making all these calls lazy:
                needles.add(unquote(needle))
                needles.add(quote(needle))
                needles.add(quote_plus(needle))
                needles.add(self.make_comp(needle))
                needles.add(self.make_comp(unquote(needle)))

            To avoid the potentially unnecessary call to self.make_comp(...)
            if the needle was found in a haystack before, making the result
            of self.make_comp(...) unnecessary.

            That would help, but the impact in real life is really small, since
            in most scenarios this method will return False, which means that
            all the comparisons need to be done anyways.

        :param needle: The string
        :return: True if something similar was sent
        """
        needle = smart_str_ignore(needle)

        needles = set()
        needles.add(needle)
        needles.add(unquote(needle))
        needles.add(quote(needle))
        needles.add(quote_plus(needle))
        needles.add(self.make_comp(needle))
        needles.add(self.make_comp(unquote(needle)))

        # Filter the short needles
        #
        # We don't want false negatives just because the string is
        # short after making comparable
        needles = {n for n in needles if len(n) >= 3}

        uri = self.get_uri()
        data = smart_str_ignore(self.get_data())
        headers = smart_str_ignore(self.get_all_headers())

        haystacks = set()
        haystacks.add(smart_str_ignore(uri))
        haystacks.add(smart_str_ignore(uri.url_decode()))
        haystacks.add(self.make_comp(smart_str_ignore(uri.url_decode())))
        haystacks.add(data)
        haystacks.add(unquote(data))
        haystacks.add(self.make_comp(data))
        haystacks.add(self.make_comp(unquote(data)))
        haystacks.add(headers)
        haystacks.add(unquote(headers))

        # Filter the short haystacks
        haystacks = {h for h in haystacks if len(h) >= 3}

        for needle in needles:
            for haystack in haystacks:
                if needle in haystack:
                    return True

        # I didn't send the needle in any way
        return False

    def __hash__(self):
        return hash(str(self.get_uri()) + self.get_data())

    def __str__(self):
        """
        :return: A string representation of this fuzzable request.
        """
        short_fmt = u'Method: %s | %s'
        long_fmt = u'Method: %s | %s | %s: (%s)'

        if self.get_raw_data():
            parameters = self.get_raw_data().get_param_names()
            dc_type = self.get_raw_data().get_type()
        else:
            parameters = self.get_uri().querystring.get_param_names()
            dc_type = self.get_uri().querystring.get_type()

        if not parameters:
            output = short_fmt % (self.get_method(), self.get_url())
        else:
            jparams = u', '.join(parameters)
            output = long_fmt % (self.get_method(), self.get_url(),
                                 dc_type, jparams)

        return output.encode(DEFAULT_ENCODING)

    def __unicode__(self):
        return str(self).decode(encoding=DEFAULT_ENCODING, errors='ignore')

    def __repr__(self):
        return '<fuzzable request | %s | %s>' % (self.get_method(),
                                                 self.get_uri())

    def __eq__(self, other):
        """
        Two requests are equal if:
            - They have the same URL
            - They have the same method
            - They have the same parameters
            - The values for each parameter is equal

        :return: True if the requests are equal.
        """
        if isinstance(other, FuzzableRequest):
            return (self.get_method() == other.get_method() and
                    self.get_uri() == other.get_uri() and
                    self.get_raw_data() == other.get_raw_data() and
                    self.get_headers() == other.get_headers())

        return False

    def get_eq_attrs(self):
        return ['_method', '_uri', '_post_data', '_headers']

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_variant_of(self, other):
        """
        Two requests are loosely equal (or variants) if:
            - They have the same URL
            - They have the same HTTP method
            - They have the same parameter names
            - The values for each parameter have the same type (int / string)

        :return: True if self and other are variants.
        """
        if self.get_method() != other.get_method():
            return False

        if self.get_url() != other.get_url():
            return False

        self_qs = self.get_uri().querystring
        other_qs = other.get_uri().querystring

        if not self_qs.is_variant_of(other_qs):
            return False

        return True

    def set_url(self, url):
        if not isinstance(url, URL):
            msg = 'The "uri" parameter of a %s must be of url.URL type.'
            raise TypeError(msg % type(self).__name__)

        self._url = URL(url.url_string.replace(' ', '%20'))
        self._uri = self._url

    def set_uri(self, uri):
        if not isinstance(uri, URL):
            msg = 'The "uri" parameter of a %s must be of url.URL type.'
            raise TypeError(msg % type(self).__name__)

        self._uri = uri
        self._url = uri.uri2url()

    def get_querystring(self):
        return self.get_uri().querystring

    def set_querystring(self, new_qs):
        self.get_uri().querystring = new_qs

    def set_method(self, method):
        self._method = method

    def set_headers(self, headers):
        if headers is not None and not isinstance(headers, Headers):
            raise TypeError(TYPE_ERROR % ('headers', 'Headers'))

        for header_name in self.REMOVE_HEADERS:
            try:
                headers.idel(header_name)
            except KeyError:
                # We don't care if they don't exist
                pass

        for k, v in self.get_default_headers().items():
            # Ignore any keys which are already defined in the user-specified
            # headers
            kvalue, kreal = headers.iget(k, None)
            if kvalue is not None:
                continue

            headers[k] = v

        self._headers = headers

    def set_referer(self, referer):
        self._headers['Referer'] = str(referer)

    def set_cookie(self, cookie):
        """
        :param cookie: A Cookie object as defined in core.data.dc.cookie,
            or a string.
        """
        if isinstance(cookie, Cookie):
            self._cookie = cookie
        elif isinstance(cookie, basestring):
            self._cookie = Cookie(cookie)
        elif cookie is None:
            self._cookie = Cookie()
        else:
            fmt = '[FuzzableRequest error] set_cookie received: "%s": "%s".'
            error_str = fmt % (type(cookie), repr(cookie))
            om.out.error(error_str)
            raise BaseFrameworkException(error_str)

    def get_url(self):
        return self._url

    def get_uri(self):
        """
        :return: The URI to send in the HTTP request
        """
        return self._uri

    def set_data(self, post_data):
        """
        Set the DataContainer which we'll use for post-data
        """
        if not isinstance(post_data, DataContainer):
            raise TypeError('The "post_data" parameter of a %s must be of '
                            'DataContainer type.' % type(self).__name__)
        self._post_data = post_data

    def get_data(self):
        """
        The data is the string representation of the post data, in most
        cases it will be used as the POSTDATA for requests.
        """
        return str(self._post_data)

    def get_raw_data(self):
        return self._post_data

    def get_method(self):
        return self._method

    def get_post_data_headers(self):
        """
        :return: A Headers object with the headers required to send the
                 self._post_data to the wire. For example, if the data is
                 url-encoded:
                    a=3&b=2

                 This method returns:
                    Content-Length: 7
                    Content-Type: application/x-www-form-urlencoded

                 When someone queries this object for the headers using
                 get_headers(), we'll include these. Hopefully this means that
                 the required headers will make it to the wire.
        """
        return Headers(init_val=self.get_raw_data().get_headers())

    def get_headers(self):
        """
        :return: The headers which can be changed by the user during fuzzing.
        :see: get_all_headers
        """
        return self._headers

    def get_all_headers(self):
        """
        :return: Calls get_default_headers to get the default framework headers,
        get_post_data_headers to get the DataContainer headers, merges that info
        with the user specified headers (which live in self._headers) and
        returns a Headers instance which will be sent to the wire.
        """
        wire_headers = Headers()

        for k, v in chain(self._headers.items(),
                          self.get_post_data_headers().items()):

            # Please note that here we're overwriting the headers from the
            # fuzzable request with the headers from the data container,
            # the overwriting is done in this order due to the order in the
            # chain() items above
            #
            # I found a bug where I loaded a request from spider_man, saved
            # it using dump() and then tried to load it again and failed because
            # of this overwriting not being done (the multipart boundary was
            # incorrect).
            #
            # Keep that in mind in case you want to change this overwriting!
            #
            # Overwrite the existing one, case insensitive style
            _, stored_header_name = wire_headers.iget(k, None)
            if stored_header_name is not None:
                wire_headers[stored_header_name] = v
            else:
                wire_headers[k] = v

        return wire_headers

    def get_referer(self):
        return self.get_headers().get('Referer', None)

    def get_cookie(self):
        return self._cookie

    def get_file_vars(self):
        """
        :return: A list of post-data parameters that contain a file
        """
        try:
            return self._post_data.get_file_vars()
        except AttributeError:
            return []
