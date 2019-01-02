"""
cookie_handler.py

Copyright 2006 Andres Riancho

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
from cookielib import MozillaCookieJar
from urllib2 import HTTPCookieProcessor


class CookieHandler(HTTPCookieProcessor):

    def __init__(self, default_cookiejar=None):
        HTTPCookieProcessor.__init__(self, None)

        # Store the different cookie jars here, these represent the different
        # browser sessions that the plugins might request
        self.jars = {}

        if default_cookiejar is None:
            default_cookiejar = MozillaCookieJar()

        self.default_cookiejar = default_cookiejar

    def get_cookie_jar(self, request):
        """
        :param request: The HTTP request, with a browser session attribute, or
                        None if the default cookiejar should be used.

        :return: The cookiejar instance
        """
        if request.session is None:
            return self.default_cookiejar

        session = self.jars.get(request.session, None)
        if session is not None:
            return session

        new_session = MozillaCookieJar()
        self.jars[request.session] = new_session
        return new_session

    def clear_cookies(self):
        """
        Clear the cookies from all cookie jars.
        :return: None
        """
        for cookiejar in self.jars.itervalues():
            cookiejar.clear()
            cookiejar.clear_session_cookies()

        self.default_cookiejar.clear()
        self.default_cookiejar.clear_session_cookies()

    def http_request(self, request):
        if not request.cookies:
            # Don't do any cookie handling
            return request

        try:
            cookiejar = self.get_cookie_jar(request)
            cookiejar.add_cookie_header(request)
        except AttributeError:
            # https://github.com/andresriancho/w3af/issues/13842
            pass

        return request

    def http_response(self, request, response):
        cookiejar = self.get_cookie_jar(request)
        cookiejar.extract_cookies(response, request)
        return response

    https_request = http_request
    https_response = http_response
