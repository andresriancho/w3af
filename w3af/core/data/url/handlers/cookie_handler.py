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
import urllib2


class CookieHandler(urllib2.HTTPCookieProcessor):

    def http_request(self, request):
        """
        I had to subclass the urllib2.HTTPCookieProcessor in order to add the
        "if request.cookies" to provide the plugins with a feature to send HTTP
        requests without any cookies.
        """
        if request.cookies:
            return urllib2.HTTPCookieProcessor.http_request(self, request)
        
        # Don't do any cookie stuff
        return request

    https_request = http_request
