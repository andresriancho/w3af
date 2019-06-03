"""
get_clean_body.py

Copyright 2018 Andres Riancho

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
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.helpers import get_clean_body_impl


def get_clean_body(response):
    """
    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/
            - response.get_body() == 'spam aaaaaaa eggs'

        - output:
            - self._clean_body( response ) == 'spam  eggs'

    The same works with file names.
    All of them, are removed url-decoded and "as is".

    :param response: The HTTPResponse object to clean
    :return: A string that represents the "cleaned" response body of the
             response.
    """
    return get_clean_body_from_parts(response.body,
                                     response.get_uri(),
                                     response.doc_type)


def get_clean_body_from_parts(body, uri, doc_type):
    """
    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/
            - response.get_body() == 'spam aaaaaaa eggs'

        - output:
            - self._clean_body( response ) == 'spam  eggs'

    The same works with file names.
    All of them, are removed url-decoded and "as is".

    :return: A string that represents the "cleaned" response body of the
             response.
    """
    if not doc_type == HTTPResponse.DOC_TYPE_TEXT_OR_HTML:
        return body

    url = uri.uri2url()

    # Do some real work...
    base_urls = [url,
                 url.switch_protocol(),
                 uri,
                 uri.switch_protocol()]

    to_replace = []

    for base_url in base_urls:
        to_replace.extend([u.url_string for u in base_url.get_directories()])
        to_replace.extend(base_url.url_string.split(u'/'))
        to_replace.extend([base_url.url_string,
                           base_url.all_but_scheme(),
                           base_url.get_path_qs(),
                           base_url.get_path()])

    # Filter some strings
    to_replace = [trs for trs in to_replace if len(trs) > 6]
    to_replace = list(set(to_replace))

    return get_clean_body_impl(body, to_replace, multi_encode=False)
