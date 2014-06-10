"""
multipart_container.py

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

from w3af.core.data.dc.generic.kv_container import KeyValueContainer


class MultipartContainer(KeyValueContainer):
    """
    This class represents a data container for multipart/post

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @staticmethod
    def is_multipart(headers):
        conttype, header_name = headers.iget('content-type', '')
        return conttype.lower().startswith('multipart/form-data')

    @classmethod
    def from_postdata(cls, headers, post_data):
        if not MultipartContainer.is_multipart(headers):
            raise ValueError('Failed to create MultipartRequest.')

        conttype, _ = headers.iget('content-type')

        try:
            pdict = cgi.parse_header(conttype)[1]
            dc = cgi.parse_multipart(StringIO.StringIO(post_data), pdict)
        except ValueError:
            raise ValueError('Failed to create MultipartRequest.')
        else:
            # Please note that the KeyValueContainer is just a container for
            # the information. When the PostDataRequest is sent it should
            # be serialized into multipart again by the MultipartPostHandler
            # because the headers contain the multipart/form-data header
            return cls(init_val=dc.items())