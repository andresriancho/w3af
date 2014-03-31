"""
helpers.py

Copyright 2013 Andres Riancho

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
from w3af.core.data.constants.response_codes import NO_CONTENT
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers

from w3af.core.controllers.misc.number_generator import consecutive_number_generator


def new_no_content_resp(uri, add_id=False):
    """
    Return a new NO_CONTENT HTTPResponse object.
    
    :param uri: URI string or request object
    """
    no_content_response = HTTPResponse(NO_CONTENT, '', Headers(), uri,
                                       uri, msg='No Content')

    if add_id:
        no_content_response.id = consecutive_number_generator.inc()

    return no_content_response