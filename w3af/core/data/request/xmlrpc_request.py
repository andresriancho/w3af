"""
XMLRPCRequest.py

Copyright 2009 Andres Riancho

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
from w3af.core.data.dc.xmlrpc import XmlRpcContainer

XMLRPC_WORDS = ('<methodcall>', '<methodname>', '<params>',
                '</methodcall>', '</methodname>', '</params>')


class XMLRPCRequest(FuzzableRequest):
    """
    This class represents a fuzzable request for a http request
    that contains XMLRPC postdata.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @staticmethod
    def is_xmlrpc(post_data):
        return all(map(lambda stop: stop in post_data.lower(), XMLRPC_WORDS))

    @classmethod
    def from_parts(cls, url, method, post_data, headers):
        if not XMLRPCRequest.is_xmlrpc(post_data):
            raise ValueError('Failed to create XMLRPCRequest.')

        try:
            container = XmlRpcContainer.from_postdata(post_data)
        except:
            raise ValueError('Failed to create XMLRPCRequest.')
        else:
            return cls(url, method=method, headers=headers,
                       post_data=container)

    def get_headers(self):
        headers = super(XMLRPCRequest, self).get_headers()
        headers['Content-Type'] = 'application/xml'
        return headers

    def set_dc(self, data_container):
        self._post_data = data_container

    def get_dc(self):
        return self._post_data

    def __str__(self):
        """
        Return a str representation of this fuzzable request.
        """
        res = '[[XMLRPC]] '
        res += self._url
        res += ' | Method: ' + self._method
        res += ' | XMLRPC: ('
        res += ','.join(self.get_dc().get_param_names())
        res += ')'
        return res

    def __repr__(self):
        return '<XMLRPC fuzzable request | %s | %s >' % (self.get_method(),
                                                         self.get_uri())
