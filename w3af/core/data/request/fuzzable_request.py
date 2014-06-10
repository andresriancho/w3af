"""
FuzzableRequest.py

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
import copy
import string

from urllib import unquote

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf

from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.kv_container import KeyValueContainer
from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.request_mixin import RequestMixIn


ALL_CHARS = ''.join(chr(i) for i in xrange(256))
TRANS_TABLE = string.maketrans(ALL_CHARS, ALL_CHARS)
DELETE_CHARS = ''.join(['\\', "'", '"', '+', ' ', chr(0), chr(int("0D", 16)),
                       chr(int("0A", 16))])


TYPE_ERROR = 'FuzzableRequest __init__ parameter %s needs to be of %s type'


class FuzzableRequest(RequestMixIn, DiskItem):
    """
    This class represents a fuzzable request. Fuzzable requests were created
    to allow w3af plugins to be much simpler and don't really care if the
    vulnerability is in the postdata, querystring, header, cookie or any other
    injection point.

    Other classes should inherit from this one and change the behaviour of
    get_dc() and set_dc(), which returns which of postdata, querystring, etc.
    is the one where we'll inject.

    This class shouldn't be used directly, please use the sub-classes:
        * HTTPQsRequest
        * PostDataRequest
        * ...

    Methods like get_uri() and get_data() shouldn't be overridden by subclasses
    (with a couple of exceptions).

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

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
    def from_parts(cls, url, method, post_data, headers):
        """
        :return: An instance of this object from the provided parameters.
        """
        raise NotImplementedError

    def export(self):
        """
        Generic version of how fuzzable requests are exported:
            METHOD,URL,POST_DATA

        Example:
            GET,http://localhost/index.php?abc=123&def=789,
            POST,http://localhost/index.php,abc=123&def=789

        :return: a csv str representation of the request
        """
        #
        # TODO: Why don't we export headers and cookies?
        #
        output = []

        for data in (self._method, self.get_uri(), self._post_data):
            output.append('"%s"' % data)

        return ','.join(output)

    def sent(self, smth_instng):
        """
        Checks if something similar to `smth_instng` was sent in the request.
        This is used to remove false positives, e.g. if a grep plugin finds a
        "strange" string and wants to be sure it was not generated by an audit
        plugin.

        This method should only be used by grep plugins which often have false
        positives.

        The following example shows that we sent d'z"0 but d\'z"0 will
        as well be recognised as sent

        TODO: This function is called MANY times, and under some circumstances
        it's performance REALLY matters. We need to review this function.

        :param smth_instng: The string
        :return: True if something similar was sent
        """
        def make_comp(heterogen_string):
            """
            This basically removes characters that are hard to compare
            """
            return string.translate(heterogen_string.encode('utf-8'),
                                    TRANS_TABLE, deletions=DELETE_CHARS)

        data = self.get_data()
        # This is the easy part. If it was exactly like this in the request
        if data and smth_instng in data or \
        smth_instng in self.get_uri() or \
        smth_instng in unquote(data) or \
        smth_instng in unicode(self._uri.url_decode()):
            return True

        # Ok, it's not in it but maybe something similar
        # Let's set up something we can compare
        if self._sent_info_comp is None:
            data_encoding = self._post_data.encoding
            post_data = str(self.get_data())
            dec_post_data = unquote(post_data).decode(data_encoding)

            data = u'%s%s%s' % (unicode(self.get_uri()), data, dec_post_data)

            self._sent_info_comp = make_comp(data + unquote(data))

        min_len = 3
        # make the smth_instng comparable
        smth_instng_comps = (make_comp(smth_instng),
                             make_comp(unquote(smth_instng)))
        for smth_intstng_comp in smth_instng_comps:
            # We don't want false negatives just because the string is
            # short after making comparable
            if smth_intstng_comp in self._sent_info_comp and \
            len(smth_intstng_comp) >= min_len:
                return True

        # I didn't sent the smth_instng in any way
        return False

    def __hash__(self):
        return hash(str(self.get_uri()))

    def __str__(self):
        """
        :return: A string representation of this fuzzable request.
        """
        strelems = [unicode(self.get_url()), u' | Method: ' + self._method]

        if self.get_dc():
            strelems.append(u' | Parameters: (')
            strelems.append(u'%s' % self.get_dc().get_short_printable_repr())
            strelems.append(u')')

        return u''.join(strelems).encode(DEFAULT_ENCODING)

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
                    self.get_data() == other.get_data() and
                    self.get_headers() == other.get_headers())
        else:
            raise NotImplementedError

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

        if not self.get_dc().is_variant_of(other.get_dc()):
            return False

        return True

    def set_url(self, url):
        if not isinstance(url, URL):
            raise TypeError('The "url" parameter of a %s must be of '
                            'url.URL type.' % type(self).__name__)

        self._url = URL(url.url_string.replace(' ', '%20'))
        self._uri = self._url

    def set_uri(self, uri):
        if not isinstance(uri, URL):
            raise TypeError('The "uri" parameter of a %s must be of '
                            'url.URL type.' % type(self).__name__)
        self._uri = uri
        self._url = uri.uri2url()

    def set_method(self, method):
        self._method = method

    def set_headers(self, headers):
        if headers is not None and not isinstance(headers, Headers):
            raise TypeError(TYPE_ERROR % ('headers', 'Headers'))

        self._headers = headers

    def set_referer(self, referer):
        self._headers['Referer'] = str(referer)

    def set_cookie(self, c):
        """
        :param cookie: A Cookie object as defined in core.data.dc.cookie,
            or a string.
        """
        if isinstance(c, Cookie):
            self._cookie = c
        elif isinstance(c, basestring):
            self._cookie = Cookie(c)
        elif c is None:
            self._cookie = Cookie()
        else:
            fmt = '[FuzzableRequest error] set_cookie received: "%s": "%s".'
            error_str = fmt % (type(c), repr(c))
            om.out.error(error_str)
            raise BaseFrameworkException(error_str)

    def get_url(self):
        return self._url

    def get_uri(self):
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

    def get_method(self):
        return self._method

    def get_dc(self):
        """
        This is saying something important to the rest of the world:
            "If you want to fuzz this request, please use the query string"

        :return: A reference to the DataContainer object which will be used for
                 fuzzing. Other sub-classes need to override this method in
                 order to allow fuzzing of headers, cookies, post-data, etc.
        """
        raise NotImplementedError

    def set_dc(self, data_container):
        """
        :note: Its really important that get_dc and set_dc both modify the same
               attribute. Each subclass of fuzzable request should modify a
               different one, to provide fuzzing functionality to that section
               of the HTTP response.

        :see: self.get_dc documentation
        """
        raise NotImplementedError

    def get_headers(self):
        """
        :return: Calls get_default_headers to get the default framework headers,
        overwrites any overlap with specific_headers and returns a Headers
        instance
        """
        for k, v in self.get_default_headers().items():
            # Ignore any keys which are already defined in the user-specified
            # headers
            kvalue, kreal = self._headers.iget(k, None)
            if kvalue is not None:
                continue

            self._headers[k] = v

        return self._headers

    def get_referer(self):
        return self.get_headers().get('Referer', None)

    def get_cookie(self):
        return self._cookie

    def get_file_vars(self):
        return []

    def copy(self):
        return copy.deepcopy(self)
