"""
multipart_request.py

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
import cgi
import StringIO

import w3af.core.controllers.output_manager as om

from w3af.core.data.dc.kv_container import KeyValueContainer
from w3af.core.data.request.post_data_request import PostDataRequest


class MultipartRequest(PostDataRequest):
    """
    This class represents a fuzzable request that sends all variables in the
    POSTDATA using multipart post encoding.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @staticmethod
    def is_multipart(headers):
        conttype, header_name = headers.iget('content-type', '')
        return conttype.lower().startswith('multipart/form-data')

    @classmethod
    def from_parts(cls, url, method, post_data, headers):
        if not MultipartRequest.is_multipart(headers):
            raise ValueError('Failed to create MultipartRequest.')

        conttype, _ = headers.iget('content-type')

        # Remove some headers which I won't need
        headers = headers.copy()
        for header_name in ('content-type', 'content-length'):
            headers.idel(header_name)

        try:
            pdict = cgi.parse_header(conttype)[1]
            dc = cgi.parse_multipart(StringIO.StringIO(post_data), pdict)
        except ValueError:
            raise ValueError('Failed to create MultipartRequest.')
        else:
            data = KeyValueContainer()
            data.update(dc)

            # Please note that the KeyValueContainer is just a container for
            # the information. When the PostDataRequest is sent it should
            # be serialized into multipart again by the MultipartPostHandler
            # because the headers contain the multipart/form-data header
            headers['content-type'] = conttype

            return cls(url, method=method, headers=headers, post_data=data)