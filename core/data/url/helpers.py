'''
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

'''
from core.data.constants.response_codes import NO_CONTENT
from core.data.url.HTTPResponse import HTTPResponse
from core.data.dc.headers import Headers

from core.controllers.misc.number_generator import consecutive_number_generator as seq_gen


def new_no_content_resp(uri):
    '''
    Return a new NO_CONTENT HTTPResponse object.
    
    :param uri: URI string or request object
    '''
    no_content_response = HTTPResponse(NO_CONTENT, '', Headers(), uri,
                                       uri, msg='No Content')

    if no_content_response.id is None:
        no_content_response.id = seq_gen.inc()

    return no_content_response