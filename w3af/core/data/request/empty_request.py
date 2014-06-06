"""
empty_request.py

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


class EmptyFuzzableRequest(FuzzableRequest):
    """
    A FuzzableRequest which can be created without knowing the URI.
    """
    def __init__(self):
        super(EmptyFuzzableRequest, self).__init__(None, method='GET',
                                                   headers=None, cookie=None,
                                                   post_data=None)

    def set_uri(self, uri):
        if uri is None:
            return

        return super(EmptyFuzzableRequest, self).set_uri(uri)