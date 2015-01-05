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
import cgi
import urllib
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


def get_clean_body(mutant, response):
    """
    @see: Very similar to fingerprint_404.py get_clean_body() bug not quite
          the same maybe in the future I can merge both?

    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/?id=1 OR 23=23
            - response.get_body() == '...<x>1 OR 23=23</x>...'

        - output:
            - self._clean_body( response ) == '...<x></x>...'

    All injected values are removed encoded and "as is".

    :param mutant: The mutant where I can get the value from.
    :param response: The HTTPResponse object to clean
    :return: A string that represents the "cleaned" response body.
    """

    body = response.body

    if response.is_text_or_html():
        mod_value = mutant.get_token_value()

        body = body.replace(mod_value, '')
        body = body.replace(urllib.unquote_plus(mod_value), '')
        body = body.replace(cgi.escape(mod_value), '')
        body = body.replace(cgi.escape(urllib.unquote_plus(mod_value)), '')

    return body