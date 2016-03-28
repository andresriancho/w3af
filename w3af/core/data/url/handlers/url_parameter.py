"""
url_parameter.py

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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest as HTTPRequest


class URLParameterHandler(urllib2.BaseHandler):
    """
    Appends a user configured URL parameter to the request URL.
    e.g.: http://www.myserver.com/index.html;jsessionid=dd18fa45014ce4fc?id=5

    See Section 2.1 URL Syntactic Components of RFC 1808
        <scheme>://<net_loc>/<path>;<params>?<query>#<fragment>
    See Section 3.2.2 of RFC 1738

    :author: Kevin Denver ( muffysw@hotmail.com )
    """

    def __init__(self, url_param):
        self._url_parameter = url_param

    def http_request(self, req):
        url_instance = URL(req.get_full_url())
        url_instance.set_param(self._url_parameter)

        new_request = HTTPRequest(url_instance,
                                  method=req.get_method(),
                                  data=req.get_data(),
                                  headers=req.get_headers(),
                                  origin_req_host=req.get_origin_req_host(),
                                  unverifiable=req.is_unverifiable(),
                                  retries=req.retries_left,
                                  cookies=req.cookies,
                                  cache=req.get_from_cache,
                                  new_connection=req.new_connection,
                                  follow_redirects=req.follow_redirects,
                                  use_basic_auth=req.use_basic_auth,
                                  use_proxy=req.use_proxy,
                                  timeout=req.timeout)
        return new_request

    https_request = http_request

