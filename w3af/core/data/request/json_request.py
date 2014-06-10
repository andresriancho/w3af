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
from w3af.core.data.dc.json_container import JSONContainer


class JSONPostDataRequest(FuzzableRequest):
    """
    This class represents a fuzzable request for a http request that contains
    JSON postdata.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @staticmethod
    def is_json(headers, post_data):
        content_type, _ = headers.iget('content-type', '')
        json_header = 'json' in content_type.lower()

        return json_header and JSONContainer.is_json(post_data)

    @classmethod
    def from_parts(cls, url, method, post_data, headers):
        if not JSONPostDataRequest.is_json(headers, post_data):
            raise ValueError('Failed to create JSONPostDataRequest.')

        try:
            data = JSONContainer.from_postdata(post_data)
        except:
            raise ValueError('Failed to create JSONPostDataRequest.')
        else:
            return cls(url, method=method, headers=headers, post_data=data)

    def set_dc(self, data_container):
        self._post_data = data_container

    def get_dc(self):
        return self._post_data

    def get_headers(self):
        headers = super(JSONPostDataRequest, self).get_headers()
        headers['Content-Type'] = 'application/json'
        return headers

    def __str__(self):
        """
        Return a str representation of this fuzzable request.
        """
        fmt = '[JSON] %s | Method: %s | JSON: (%s)'
        return fmt % (self.get_url(), self.get_method(),
                      ','.join(self.get_dc().get_param_names()))

    def __repr__(self):
        return '<JSON fuzzable request | %s | %s >' % (self.get_method(),
                                                       self.get_uri())
