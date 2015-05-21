"""
HTTPRequest.py

Copyright 2010 Andres Riancho

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
import socket
import urllib2

from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.request_mixin import RequestMixIn
from w3af.core.data.url.constants import MAX_HTTP_RETRIES


class HTTPRequest(RequestMixIn, urllib2.Request):

    def __init__(self, url, data=None, headers=Headers(),
                 origin_req_host=None, unverifiable=False,
                 cookies=True, cache=False, method=None,
                 error_handling=True, retries=MAX_HTTP_RETRIES,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT, new_connection=False):
        """
        This is a simple wrapper around a urllib2 request object which helps
        with some common tasks like serialization, cache, etc.

        :param method: None means choose the default (POST if data is not None)
        :param data: The post_data as a string
        """
        #
        # Save some information for later access in an easier way
        #
        self.url_object = url
        self.cookies = cookies
        self.get_from_cache = cache
        self.error_handling = error_handling
        self.retries_left = retries
        self.timeout = timeout
        self.new_connection = new_connection

        self.method = method
        if self.method is None:
            self.method = 'POST' if data else 'GET'

        if isinstance(headers, Headers):
            headers.tokens_to_value()
            
        headers = dict(headers)

        # Call the base class constructor
        urllib2.Request.__init__(self, url.url_encode(), data,
                                 headers, origin_req_host, unverifiable)
        RequestMixIn.__init__(self)
    
    def __eq__(self, other):
        return self.get_method() == other.get_method() and \
               self.get_uri() == other.get_uri() and \
               self.get_headers() == other.get_headers() and \
               self.get_data() == other.get_data() and \
               self.get_timeout() == other.get_timeout()

    def add_header(self, key, val):
        """
        Override mostly to avoid having header values of DataToken type

        :param key: The header name as a string
        :param val: The header value (a string of a DataToken)
        :return: None
        """
        if isinstance(val, DataToken):
            val = val.get_value()

        self.headers[key.capitalize()] = val

    def get_method(self):
        return self.method

    def set_method(self, method):
        self.method = method
            
    def get_uri(self):
        return self.url_object
    
    def get_headers(self):
        headers = Headers(self.headers.items())
        headers.update(self.unredirected_hdrs.items())
        return headers

    def set_headers(self, headers):
        self.headers = dict(headers)

    def get_timeout(self):
        return self.timeout
    
    def to_dict(self):
        serializable_dict = {}
        sdict = serializable_dict
        
        sdict['method'] = self.get_method()
        sdict['uri'] = self.get_uri().url_string
        sdict['headers'] = dict(self.get_headers())
        sdict['data'] = self.get_data()
        sdict['cookies'] = self.cookies
        sdict['cache'] = self.get_from_cache
        sdict['timeout'] = None if self.timeout is socket._GLOBAL_DEFAULT_TIMEOUT else self.timeout
        sdict['new_connection'] = self.new_connection
            
        return serializable_dict

    @classmethod
    def from_fuzzable_request(cls, fuzzable_request):
        """
        :param fuzzable_request: The FuzzableRequest
        :return: An instance of HTTPRequest with all the information contained
                 in the FuzzableRequest passed as parameter
        """
        host = fuzzable_request.get_url().get_domain()
        data = fuzzable_request.get_data()
        headers = fuzzable_request.get_headers()
        headers.tokens_to_value()

        return cls(fuzzable_request.get_uri(), data=data, headers=headers,
                   origin_req_host=host)

    @classmethod    
    def from_dict(cls, unserialized_dict):
        """
        * msgpack is MUCH faster than cPickle,
        * msgpack can't serialize python objects,
        * I have to create a dict representation of HTTPRequest to serialize it,
        * and a from_dict to have the object back
        
        :param unserialized_dict: A dict just as returned by to_dict()
        """
        udict = unserialized_dict
        
        method, uri = udict['method'], udict['uri']
        headers, data = udict['headers'], udict['data']
        cookies = udict['cookies']
        cache = udict['cache']
        timeout = socket._GLOBAL_DEFAULT_TIMEOUT if udict['timeout'] is None else udict['timeout']
        new_connection = udict['new_connection']

        headers_inst = Headers(headers.items())
        url = URL(uri)
        
        return cls(url, data=data, headers=headers_inst,
                   cookies=cookies, cache=cache, method=method,
                   timeout=timeout, new_connection=new_connection)

    def copy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        fmt = '<HTTPRequest "%s" (cookies:%s, cache:%s)>'
        return fmt % (self.url_object.url_string, self.cookies,
                      self.get_from_cache)
