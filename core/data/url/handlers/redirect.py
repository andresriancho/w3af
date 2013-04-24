'''
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

'''
import urllib2


class HTTP30XHandler(urllib2.HTTPDefaultErrorHandler):
    '''
    A simple handler that says: "30x responses are not errors".
    
    Please note that this is NOT an HTTPRedirectHandler. We do NOT want to
    follow any HTTP redirects in an "automagic" way. If the user/plugin needs
    to follow a redirect he needs to do it manually.
    
    In cases such as the web_spider.py this is not an issue since it will
    perform an HTTP request and then create the fuzzable requests:
    
        resp = self._uri_opener.send_mutant(fuzzable_req)

        fuzz_req_list = self._create_fuzzable_requests(
            resp,
            request=fuzzable_req,
            add_self=False
        )
    
    If the "resp" object in that code is a 302, the _create_fuzzable_requests
    will take care of parsing the "Location" header and returning a fuzzable
    request (in fuzz_req_list) for it.
    '''
    def http_error_default(self, req, resp, code, msg, hdrs):
        m = req.get_method()
        if (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
        or code in (301, 302, 303) and m == "POST"):
            _30X_resp = urllib2.addinfourl(resp, msg, req.get_full_url())
            _30X_resp.code = code
            _30X_resp.msg = msg
            _30X_resp.headers = hdrs
            _30X_resp.id = req.id
            _30X_resp.encoding = getattr(resp, 'encoding', None)
            return _30X_resp

        err = urllib2.HTTPError(req.get_full_url(), code, msg, hdrs, resp)
        err.id = req.id
        raise err
