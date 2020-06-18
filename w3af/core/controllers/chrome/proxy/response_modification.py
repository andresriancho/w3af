"""
response_modification.py

Copyright 2019 Andres Riancho

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

SECURITY_HEADERS = {'Strict-Transport-Security',
                    'Public-Key-Pins',
                    'Content-Security-Policy',
                    'Upgrade-Insecure-Requests'}


def set_content_encoding(http_response):
    """
    This is an important step! The ExtendedUrllib will gunzip the body
    for us, which is great, but we need to change the content-encoding
    for the response in order to match the decoded body and avoid the
    HTTP client using the proxy from failing

    :param http_response: The HTTP response to modify
    """
    headers = http_response.get_headers()

    #
    # Remove this one...
    #
    _, stored_header_name = headers.iget('transfer-encoding')

    if stored_header_name is not None:
        headers.pop(stored_header_name)

    #
    # Replace this one...
    #
    _, stored_header_name = headers.iget('content-encoding')

    if stored_header_name is not None:
        headers.pop(stored_header_name)

    headers['content-encoding'] = 'identity'


def remove_security_headers(http_response):
    """
    Remove the security headers which increase the application security on
    run-time (when run by the browser). These headers are things like HSTS
    and CSP.

    We remove them in order to prevent CSP errors from blocking our tests,
    HSTS from breaking mixed content, etc.
    """
    headers = http_response.get_headers()

    for security_header in SECURITY_HEADERS:
        _, stored_header_name = headers.iget(security_header)

        if stored_header_name is not None:
            headers.pop(stored_header_name)

