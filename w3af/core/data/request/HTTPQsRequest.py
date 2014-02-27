"""
HTTPQsRequest.py

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
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.headers import Headers


class HTTPQSRequest(FuzzableRequest):
    """
    This class represents a fuzzable request that sends all variables
    in the querystring. This is tipically used for GET requests.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, uri, method='GET', headers=Headers(), cookie=None):
        super(HTTPQSRequest, self).__init__(uri, method, headers, cookie)

    def set_uri(self, uri):
        """
        >>> r = HTTPQSRequest('http://www.w3af.com/')
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        TypeError: The "uri" parameter of a HTTPQSRequest must be of url.URL type.
        >>> from w3af.core.data.parsers.url import URL
        >>> r = HTTPQSRequest(URL('http://www.w3af.com/'))
        >>> uri = URL('http://www.w3af.com/scan')
        >>> r.set_uri(uri)
        >>> r.get_uri() == uri
        True
        """
        super(HTTPQSRequest, self).set_uri(uri)
        self._dc = self._uri.querystring

    def get_uri(self):
        uri = self._url.copy()
        if self._dc:
            uri.querystring = self._dc
        return uri

    def set_data(self, d):
        pass

    def set_method(self, meth):
        pass

    def get_data(self):
        # The postdata
        return None

    def __repr__(self):
        return ('<QS fuzzable request | %s | %s>' %
                (self.get_method(), self.get_uri()))
