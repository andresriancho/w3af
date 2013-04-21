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
import urlparse

from core.controllers.misc.number_generator import \
    consecutive_number_generator as core_num_gen
from core.data.parsers.url import URL
from core.data.url.HTTPRequest import HTTPRequest as HTTPRequest


class HTTP30XHandler(urllib2.HTTPRedirectHandler):

    def _inc_counter(self, step=1):
        '''
        :return: The next number to use in the request/response ID.
        '''
        return core_num_gen.inc()

    def _get_counter(self):
        '''
        :return: The current counter number to assign as the id for responses.
        '''
        return core_num_gen.get()

    def http_error_302(self, req, fp, code, msg, headers):
        '''
        This is a http_error_302 wrapper to add an id attr to loop errors.
        '''
        if not req.follow_redir:
            return None

        try:
            return self._http_error_302(req, fp, code, msg, headers)
        except urllib2.HTTPError, e:
            #om.out.debug('The remote web application generated a redirect '
            #             'loop when requesting: %s' % e.geturl())
            e.id = self._get_counter()
            raise e

    http_error_301 = http_error_303 = http_error_307 = http_error_302

    # FIXME: A duplicated and slightly modified (see comment below)
    # version of urllib2.HTTPRedirectHandler.http_error_302 method. This
    # code duplication must be removed once the cause disappears (in py2.6.5
    # still present) and call instead the original one.
    def _http_error_302(self, req, fp, code, msg, headers):
        # Some servers (incorrectly) return multiple Location headers
        # (so probably same goes for URI).  Use first header.
        if 'location' in headers:
            newurl = headers.getheaders('location')[0]
        elif 'uri' in headers:
            newurl = headers.getheaders('uri')[0]
        else:
            return

        # fix a possible malformed URL
        # pylint: disable=E1101
        urlparts = urlparse.urlparse(newurl)
        if not urlparts.path:
            urlparts = list(urlparts)
            urlparts[2] = "/"
        newurl = urlparse.urlunparse(urlparts)

        newurl = urlparse.urljoin(req.get_full_url(), newurl)

        # XXX HACK! The reason for overriding (and also duplicating content)
        # this method was to fix a bug in the urllib2 handler where you might
        # end up being redirected to some "strange" location if for some
        # reason the value of "location" is C:\boot.ini, and you
        # urlparse.urljoin the current URL with that one, you end up with
        # C:\boot.ini. When the urllib2 library opens that, it will open a
        # local file. Verifying that the protocol of the newurl is 'http[s]'
        # was the implemented solution.
        correct_protocol = (newurl.startswith('http://') or
                            newurl.startswith('https://'))
        if not correct_protocol:
            return

        # XXX Probably want to forget about the state of the current
        # request, although that might interact poorly with other
        # handlers that also use handler-specific request attributes
        new = self.redirect_request(req, fp, code, msg, headers, newurl)
        if new is None:
            return

        # loop detection
        # .redirect_dict has a key url if url was previously visited.
        if hasattr(req, 'redirect_dict'):
            visited = new.redirect_dict = req.redirect_dict
            if (visited.get(newurl, 0) >= self.max_repeats or
                    len(visited) >= self.max_redirections):
                raise urllib2.HTTPError(req.get_full_url(), code,
                                        self.inf_msg + msg, headers, fp)
        else:
            visited = new.redirect_dict = req.redirect_dict = {}
        visited[newurl] = visited.get(newurl, 0) + 1

        # Don't close the fp until we are sure that we won't use it
        # with HTTPError.
        fp.read()
        fp.close()

        return self.parent.open(new, timeout=req.timeout)

    # This was added for some special cases where the redirect
    # handler cries a lot... Again, pretty much code duplication
    # from parent class
    def redirect_request(self, req, resp, code, msg, headers, newurl):
        '''
        Return a Request or None in response to a redirect.

        This is called by the http_error_30x methods when a
        redirection response is received.  If a redirection should
        take place, return a new Request to allow http_error_30x to
        perform the redirect.  Otherwise, raise HTTPError if no-one
        else should try to handle this url.  Return None if you can't
        but another Handler might.
        '''
        m = req.get_method()
        if (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
        or code in (301, 302, 303) and m == "POST"):
            # Strictly (according to RFC 2616), 301 or 302 in response
            # to a POST MUST NOT cause a redirection without confirmation
            # from the user (of urllib2, in this case).  In practice,
            # essentially all clients do redirect in this case, so we
            # do the same.

            if 'Content-length' in req.headers:
                req.headers.pop('Content-length')

            enc = req.url_object.encoding

            new_request = HTTPRequest(
                URL(newurl.decode(
                    enc, 'ignore'), encoding=enc),
                headers=req.headers,
                origin_req_host=req.get_origin_req_host(),
                unverifiable=True
            )

            return new_request
        else:
            err = urllib2.HTTPError(req.get_full_url(),
                                    code, msg, headers, resp)
            err.id = self._inc_counter()
            raise err


class HTTPErrorHandler(urllib2.HTTPDefaultErrorHandler):

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
