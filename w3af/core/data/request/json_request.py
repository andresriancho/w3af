"""
json_request.py

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


class JSONPostDataRequest(FuzzableRequest):
    """
    This class represents a fuzzable request for a http request that contains
    JSON postdata.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def set_dc(self, data_container):
        self._post_data = data_container

    def get_dc(self):
        return self._post_data

    def __str__(self):
        """
        Return a str representation of this fuzzable request.
        """
        str_res = '[[JSON]] '
        str_res += self._url
        str_res += ' | Method: ' + self._method
        str_res += ' | JSON: ('
        str_res += ','.join(self.get_dc().get_param_names())
        str_res += ')'
        return str_res

    def __repr__(self):
        return '<JSON fuzzable request | %s | %s >' % (self.get_method(),
                                                       self.get_uri())
