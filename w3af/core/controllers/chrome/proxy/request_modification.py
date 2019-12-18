"""
request_modification.py

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
import re


DEFAULT_LANGUAGE = 'en-GB,en-US;q=0.9,en;q=0.8'
HEADLESS_RE = re.compile('HeadlessChrome/.*? ')


def add_language_header(http_request):
    """
    Some sites require the accept-language header to be sent in the HTTP
    request.

    https://github.com/GoogleChrome/puppeteer/issues/665
    https://github.com/GoogleChrome/puppeteer/issues/665#issuecomment-356634721

    Also, some sites use this header to identify headless chrome and change
    the behavior to (in most cases) prevent scrapping.

    This method adds the accept-language header if it is not already set.

    :param http_request: HTTP request
    :return: HTTP request with the header
    """
    headers = http_request.get_headers()

    stored_header_value, stored_header_name = headers.iget('accept-language')

    if stored_header_name is not None:
        # Already set, just return
        return

    headers['Accept-Language'] = DEFAULT_LANGUAGE
    http_request.set_headers(headers)


def remove_user_agent_headless(http_request):
    """
    Remove the HeadlessChrome part of the user agent string.

    Some sites detect this and block it.

    https://github.com/GoogleChrome/puppeteer/issues/665

    :param http_request: HTTP request
    :return: HTTP request
    """
    headers = http_request.get_headers()

    stored_header_value, stored_header_name = headers.iget('user-agent')

    if not stored_header_name:
        return

    mo = HEADLESS_RE.search(stored_header_value)
    if not mo:
        return

    headless_part = mo.group(0)

    without_headless = stored_header_value.replace(headless_part, '')
    headers[stored_header_name] = without_headless

    http_request.set_headers(headers)
