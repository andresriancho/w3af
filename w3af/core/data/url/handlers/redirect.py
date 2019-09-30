"""
redirect.py

Copyright 2011 Andres Riancho

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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest

GET_HEAD_CODES = {301, 302, 303, 307}
GET_HEAD = {'GET', 'HEAD'}

POST_CODES = {301, 302, 303}
POST = 'POST'

REMOVE_ON_REDIRECT = {'content-length', 'content-type'}
LOCATION = 'location'
URI = 'uri'


class HTTP30XHandler(urllib2.HTTPRedirectHandler):
    """
    A simple handler that handles 30x HTTP responses when the request has
    `follow_redirects` set to True.

    The handler follows the redirect to the next URL, keeping track of redirect
    loops.

    Most plugins don't care about redirects and thus the default follow_redirect
    setting is False. In cases such as the web_spider.py this is not an issue
    since it will perform an HTTP request and then create the fuzzable requests
    in headers_url_generator
    """

    def create_redirect_request(self, request, response, new_url_obj):
        """
        Create a new HTTP request inheriting all the attributes from the
        original object and setting the target URL to the one received in the
        30x response.
        """
        new_headers = dict((k, v) for k, v in request.headers.items()
                           if k.lower() not in REMOVE_ON_REDIRECT)

        orig_method = request.get_method()
        method = orig_method if orig_method in GET_HEAD else 'GET'

        new_request = HTTPRequest(new_url_obj,
                                  headers=new_headers,
                                  origin_req_host=request.get_origin_req_host(),
                                  method=method,
                                  timeout=request.timeout,
                                  unverifiable=True,
                                  follow_redirects=True,
                                  cookies=request.cookies,
                                  cache=request.get_from_cache,
                                  error_handling=request.error_handling,
                                  retries=request.retries_left,
                                  new_connection=request.new_connection,
                                  use_basic_auth=request.use_basic_auth)

        return new_request

    def do_follow_redirect(self, request, response):
        """
        Implementation note: To avoid the server sending us into an
        infinite loop, the request object needs to track what URLs we
        have already seen.  Do this by adding a handler-specific
        attribute to the Request object.
        """
        headers = response.info()

        #
        # Some servers incorrectly return multiple `Location` headers
        # (so probably same goes for URI). Use first header
        #
        if LOCATION in headers:
            new_url_raw = headers.getheaders(LOCATION)[0]
        elif URI in headers:
            new_url_raw = headers.getheaders(URI)[0]
        else:
            # There is no location or uri headers
            # Return the original response and continue
            return response

        #
        # Calculate the target URL using urljoin()
        #
        try:
            current_url = URL(request.get_full_url())
            new_url_obj = current_url.url_join(new_url_raw)
            new_url_str = new_url_obj.url_string
        except ValueError:
            # The target URI seems to be invalid
            # Return the original response and continue
            return response

        #
        # For security reasons we do not allow redirects to protocols
        # other than HTTP or HTTPS
        #
        new_url_lower = new_url_str.lower()
        if not (new_url_lower.startswith('http://') or
                new_url_lower.startswith('https://')):
            # The target URI seems to be pointing to file:// or ftp://
            # Return the original response and continue
            return response

        # XXX Probably want to forget about the state of the current
        # request, although that might interact poorly with other
        # handlers that also use handler-specific request attributes
        new_request = self.create_redirect_request(request, response, new_url_obj)

        # loop detection
        # .redirect_dict has a key url if url was previously visited.
        if hasattr(request, 'redirect_dict'):
            visited = new_request.redirect_dict = request.redirect_dict

            if visited.get(new_url_str, 0) >= self.max_repeats:
                # Already visited the same URL more than max_repeats
                # Return the original response and continue
                return response

            if len(visited) >= self.max_redirections:
                # Already visited more than max_redirections during this process
                # Return the original response and continue
                return response
        else:
            visited = new_request.redirect_dict = request.redirect_dict = {}

        visited[new_url_str] = visited.get(new_url_str, 0) + 1

        #
        # Send the new HTTP request to the opener
        #
        return self.parent.open(new_request)

    def redirect_allowed_by_rfc(self, request, response):
        """
        The RFC defines only some cases in which the HTTP response can
        return 30x codes, and which codes can be returned.

        :return: True if we can redirect
        """
        method = request.get_method()
        code = response.code

        # Strictly (according to RFC 2616), 301 or 302 in response
        # to a POST MUST NOT cause a redirection without confirmation
        # from the user (of urllib2, in this case).  In practice,
        # essentially all clients do redirect in this case, so we
        # do the same.
        if code in GET_HEAD_CODES and method in GET_HEAD:
            return True

        if code in POST_CODES and method == POST:
            return True

        return False

    def http_response(self, request, response):
        """
        This is the entry point for the handler.

        Receive an HTTP request and response, and decides if it should follow
        the redirection or not.
        """
        follow_redirects = getattr(request, 'follow_redirects', False)

        if not follow_redirects:
            # Do not follow any redirects, just return the original response
            return response

        #
        # Follow 30x redirect by performing one or more requests
        #
        if self.redirect_allowed_by_rfc(request, response):
            return self.do_follow_redirect(request, response)

        return response
    
    https_response = http_response

