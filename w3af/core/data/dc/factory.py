# -*- coding: utf8 -*-
"""
factory.py

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
from w3af.core.data.dc.form import Form
from w3af.core.data.dc.json_container import JSONContainer
from w3af.core.data.dc.xmlrpc import XmlRpcContainer
from w3af.core.data.dc.multipart_container import MultipartContainer
from w3af.core.data.dc.headers import Headers

# Form is at the end on purpose, since its the one which has a "wildcard match"
# for catching almost everything we don't know how to properly parse
POST_DATA_CONTAINERS = (MultipartContainer, JSONContainer, XmlRpcContainer,
                        Form)


def dc_factory(headers, post_data):
    """
    :param headers: HTTP request headers, most importantly containing the
                    content-type info.
    :param post_data: The HTTP request post-data as a string
    :return: The best-match from POST_DATA_CONTAINERS to hold the information
             in self._post_data @ FuzzableRequest
    """
    if headers is None:
        headers = Headers()

    for pdc_klass in POST_DATA_CONTAINERS:
        try:
            return pdc_klass.from_postdata(headers, post_data)
        except (ValueError, TypeError) as e:
            pass

    content_type, _ = headers.iget('content-type', 'missing')
    raise ValueError('Unknown post-data. Content-type: %s' % content_type)