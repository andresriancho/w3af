"""
JSONRequest.py

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
import json

from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest


class JSONPostDataRequest(HTTPPostDataRequest):
    """
    This class represents a fuzzable request for a http request that contains
    JSON postdata.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def get_data(self):
        """
        :return: A string that represents the JSON data saved in the dc.
        """
        return json.dumps(self._dc)

    def __str__(self):
        """
        Return a str representation of this fuzzable request.
        """
        str_res = '[[JSON]] '
        str_res += self._url
        str_res += ' | Method: ' + self._method
        str_res += ' | JSON: ('
        str_res += json.dumps(self._dc)
        str_res += ')'
        return str_res

    def set_dc(self, data_cont):
        self._dc = data_cont

    def __repr__(self):
        return '<JSON fuzzable request | ' + self.get_method() + ' | ' + self.get_uri() + ' >'
