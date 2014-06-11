"""
urlencoded_post_request.py

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
from w3af.core.data.parsers.url import parse_qs
from w3af.core.data.request.post_data_request import PostDataRequest


class URLEncPostRequest(PostDataRequest):
    """
    This class represents a fuzzable request that sends all variables in the
    POSTDATA using urlencoding.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    ENCODING = 'application/x-www-form-urlencoded'

    @staticmethod
    def is_urlencoded(headers):
        conttype, header_name = headers.iget('content-type', '')
        return URLEncPostRequest.ENCODING in conttype.lower()

    @classmethod
    def from_parts(cls, url, method, post_data, headers):
        if not URLEncPostRequest.is_urlencoded(headers):
            raise ValueError('Failed to create URLEncPostRequest.')

        try:
            data = parse_qs(post_data)
        except:
            raise ValueError('Failed to create URLEncPostRequest.')
        else:
            return cls(url, method=method, headers=headers, post_data=data)