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
    A simple handler that does two things:

        1- When the request set follow_redirects to False and the response is
           a 30x response it does the required work so that urllib2 does not
           think that it's an error.

        2- When the request set follow_redirects to True and the response is
           a 30x response it follows the redirect to the next URL, keeping
           track of redirect loops.

    Most plugins don't care about redirects and thus the default follow_redirect
    setting is False. In cases such as the web_spider.py this is not an issue
    since it will perform an HTTP request and then create the fuzzable requests
    in headers_url_generator
    """

    def create_redirect_request(self, req, fp, code, msg, headers, new_url_str,
                                new_url_obj):
        """
        This is called by the http_error_30x methods when a
        redirection response is received.  If a redirection should
        take place, return a new Request to allow http_error_30x to
        perform the redirect.
        """
        new_headers = dict((k, v) for k, v in req.headers.items()
                           if k.lower() not in REMOVE_ON_REDIRECT)

        orig_method = req.get_method()
        method = orig_method if orig_method in {'GET', 'HEAD'} else 'GET'

        new_request = HTTPRequest(new_url_obj,
                                  headers=new_headers,
                                  origin_req_host=req.get_origin_req_host(),
                                  method=method,
                                  timeout=req.timeout,
                                  unverifiable=True,
                                  follow_redirects=True,
                                  cookies=req.cookies,
                                  cache=req.get_from_cache,
                                  error_handling=req.error_handling,
                                  retries=req.retries_left,
                                  new_connection=req.new_connection,
                                  use_basic_auth=req.use_basic_auth)

        return new_request

    def do_follow_redirect(self, req, fp, code, msg, headers):
        """
        Implementation note: To avoid the server sending us into an
        infinite loop, the request object needs to track what URLs we
        have already seen.  Do this by adding a handler-specific
        attribute to the Request object.
        """

        # Check if we can redirect according to the RFC
        if not self.redirect_allowed_by_rfc(req, code):
            raise self.create_error_from_parts(req, code, msg, headers, fp)

        # Some servers (incorrectly) return multiple Location headers
        # (so probably same goes for URI). Use first header.
        if LOCATION in headers:
            new_url_raw = headers.getheaders(LOCATION)[0]
        elif URI in headers:
            new_url_raw = headers.getheaders(URI)[0]
        else:
            raise self.create_error_from_parts(req, code, msg, headers, fp)

        # Calculate the target URL
        try:
            current_url = URL(req.get_full_url())
            new_url_str = current_url.url_join(new_url_raw).url_string
            new_url_obj = current_url.url_join(new_url_raw)
        except ValueError:
            raise self.create_error_from_parts(req, code, msg, headers, fp)

        # For security reasons we do not allow redirects to protocols
        # other than HTTP or HTTPS
        new_url_lower = new_url_str.lower()
        if not (new_url_lower.startswith('http://') or
                new_url_lower.startswith('https://')):
            raise self.create_error_from_parts(req, code, msg, headers, fp)

        # XXX Probably want to forget about the state of the current
        # request, although that might interact poorly with other
        # handlers that also use handler-specific request attributes
        new_request = self.create_redirect_request(req, fp, code, msg,
                                                   headers, new_url_str,
                                                   new_url_obj)

        # loop detection
        # .redirect_dict has a key url if url was previously visited.
        if hasattr(req, 'redirect_dict'):
            visited = new_request.redirect_dict = req.redirect_dict
            if (visited.get(new_url_str, 0) >= self.max_repeats or
                len(visited) >= self.max_redirections):
                raise self.create_error_from_parts(req, code, msg, headers, fp)
        else:
            visited = new_request.redirect_dict = req.redirect_dict = {}

        visited[new_url_str] = visited.get(new_url_str, 0) + 1

        # Don't close the fp until we are sure that we won't use it
        # with HTTPError.
        fp.read()
        fp.close()

        return self.parent.open(new_request, timeout=req.timeout)

    def redirect_allowed_by_rfc(self, req, code):
        """
        The RFC defines only some cases in which the HTTP response can
        return 30x codes, and which codes can be returned.

        :return: True if we can redirect
        """
        m = req.get_method()

        # Strictly (according to RFC 2616), 301 or 302 in response
        # to a POST MUST NOT cause a redirection without confirmation
        # from the user (of urllib2, in this case).  In practice,
        # essentially all clients do redirect in this case, so we
        # do the same.
        if (code in GET_HEAD_CODES and m in GET_HEAD)\
        or (code in POST_CODES and m == POST):
            return True

        return False

    def create_error_from_parts(self, req, code, msg, hdrs, resp):
        """
        Use the different parts of the request and response to create an error
        and return it.
        """
        err = urllib2.HTTPError(req.get_full_url(), code, msg, hdrs, resp)
        err.id = req.id
        return err

    def http_error_default(self, req, resp, code, msg, hdrs):
        """
        This is the entry point for the handler, it takes a request and response
        and decides if it should follow the redirection or not.
        """
        follow_redirects = getattr(req, 'follow_redirects', False)

        if not follow_redirects:
            #
            # Do not follow any redirects, just handle the response and any
            # errors according to the RFC
            #
            if self.redirect_allowed_by_rfc(req, code):
                return resp

            raise self.create_error_from_parts(req, code, msg, hdrs, resp)

        else:
            #
            # Follow 30x redirect by performing one or more requests
            #
            return self.do_follow_redirect(req, resp, code, msg, hdrs)
    
    http_error_301 = http_error_302 = http_error_303 = http_error_307 = http_error_default
