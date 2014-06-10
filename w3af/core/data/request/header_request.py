"""
header_request.py

Copyright 2014 Andres Riancho

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


class HeaderRequest(FuzzableRequest):
    """
    This class represents a fuzzable request that allows the user to easily
    modify HTTP request headers.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @classmethod
    def from_parts(cls, url, method, post_data, headers):
        # We want to modify HTTP headers only in GET+QS requests
        if post_data:
            raise ValueError('Failed to create HeaderRequest.')

        if method != 'GET':
            raise ValueError('Failed to create HeaderRequest.')

        return cls(url, method=method, headers=headers, post_data=None)

    def get_dc(self):
        """
        This is saying something important to the rest of the world:
            "If you want to fuzz this request, please use the query string"

        :return: A reference to the DataContainer object which will be used for
                 fuzzing. Other sub-classes need to override this method in
                 order to allow fuzzing of headers, cookies, post-data, etc.
        """
        return self.get_headers()

    def set_dc(self, data_container):
        """
        :note: Its really important that get_dc and set_dc both modify the same
               attribute. Each subclass of fuzzable request should modify a
               different one, to provide fuzzing functionality to that section
               of the HTTP response.

        :see: self.get_dc documentation
        """
        self.set_headers(data_container)

    def __repr__(self):
        return ('<QS fuzzable request | %s | %s>' %
                (self.get_method(), self.get_uri()))
