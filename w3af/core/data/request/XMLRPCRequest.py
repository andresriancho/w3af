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
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from w3af.core.data.parsers.xmlrpc import parse_xmlrpc, build_xmlrpc
from w3af.core.data.dc.headers import Headers


class XMLRPCRequest(HTTPPostDataRequest):
    """
    This class represents a fuzzable request for a http request
    that contains XMLRPC postdata.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, xml, uri, method='POST', headers=Headers()):
        """
        :param xml: The original XML string that represents
                    the call to the RPC.
        """
        HTTPPostDataRequest.__init__(self, uri)
        self._xml = xml

    def get_data(self):
        """
        :return: A string that represents the XMLRPC data saved in the dc.
        """
        return build_xmlrpc(self._xml, self._dc)

    def __str__(self):
        """
        Return a str representation of this fuzzable request.
        """
        res = '[[XMLRPC]] '
        res += self._url
        res += ' | Method: ' + self._method
        res += ' | XMLRPC: ('
        res += ','.join([i[1] for i in parse_xmlrpc(self._xml).all_parameters])
        res += ')'
        return res

    def set_dc(self, data_container):
        self._dc = data_container

    def __repr__(self):
        return '<XMLRPC fuzzable request | ' + self.get_method() + ' | ' + self.get_uri() + ' >'
