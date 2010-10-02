'''
logHandler.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

import core.controllers.outputManager as om

import core.data.url.httpResponse as httpResponse
from core.data.url.HTTPRequest import HTTPRequest as HTTPRequest

import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.controllers.misc.number_generator import consecutive_number_generator
from core.data.request.frFactory import createFuzzableRequestRaw


class logHandler(urllib2.BaseHandler, urllib2.HTTPDefaultErrorHandler, urllib2.HTTPRedirectHandler):
    """
    Add an unique id attribute to http responses and then log them.
    """
    
    handler_order = urllib2.HTTPErrorProcessor.handler_order -1
    
    def __init__(self):
        pass
    
    def inc_counter( self, step=1 ):
        '''
        @return: The next number to use in the request/response ID.
        '''
        return consecutive_number_generator.inc()
            
    def _get_counter( self ):
        '''
        @return: The current counter number to assign as the id for responses.
        '''
        return consecutive_number_generator.get()

    def http_error_default(self, req, fp, code, msg, hdrs):
        err = urllib2.HTTPError(req.get_full_url(), code, msg, hdrs, fp)
        err.id = req.id
        raise err

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        '''
        This was added for some special cases where the redirect handler cries a lot...

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
            
            # This path correctly assigns a id for the request/response
            newurl = newurl.replace(' ', '%20')
            if 'Content-length' in req.headers:
                req.headers.pop('Content-length')
            
            new_request = HTTPRequest(newurl,
            headers=req.headers,
            origin_req_host=req.get_origin_req_host(),
            unverifiable=True)
            
            return new_request
        else:
            err = urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
            err.id = self.inc_counter()
            raise err
    
    inf_msg = "The HTTP server returned a redirect error that would " \
              "lead to an infinite loop.\n" \
              "The last 30x error message was:\n"
              
    # Implementation note: To avoid the server sending us into an
    # infinite loop, the request object needs to track what URLs we
    # have already seen.  Do this by adding a handler-specific
    # attribute to the Request object.
    def original_http_error_302(self, req, fp, code, msg, headers):
        # Some servers (incorrectly) return multiple Location headers
        # (so probably same goes for URI).  Use first header.
        if 'location' in headers:
            newurl = headers.getheaders('location')[0]
        elif 'uri' in headers:
            newurl = headers.getheaders('uri')[0]
        else:
            return
        newurl = urlparse.urljoin(req.get_full_url(), newurl)
        
        #
        #   The whole reason of overriding this method was to fix a bug in the urllib2
        #   handler where you might end up being redirected to some "strange" location
        #   if for some reason the value of "location" is C:\boot.ini, and you urlparse.urljoin
        #   the current URL with that one, you end up with C:\boot.ini . When the urllib2
        #   library opens that, it will open a local file. What I did to fix it, is to verify that
        #   the protocol of the newurl is http or https.
        #
        correct_protocol = newurl.startswith('http://')  or newurl.startswith('https://') 
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

        return self.parent.open(new)

    def http_error_302(self, req, fp, code, msg, headers):
        '''
        This is a http_error_302 wrapper to add an id attr to loop errors.
        '''
        id_for_error = self._get_counter()
        try:
            return self.original_http_error_302(req, fp, code, msg, headers)
        except urllib2.HTTPError, e:
            #om.out.debug('The remote web application generated a redirect loop when requesting: ' + \
            #e.geturl() )
            e.id = id_for_error
            raise e
        
    http_error_301 = http_error_303 = http_error_307 = http_error_302 = http_error_302
    
    def http_request(self, request):
        '''
        perform some ugly hacking of request headers and go on...
        '''
        #
        # FIXME: What if the user doesn't want to add these headers?
        #
        if not request.has_header('Host'):
            request.add_unredirected_header('Host', request.host )
            
        if not request.has_header('Accept-Encoding'):
            request.add_unredirected_header('Accept-Encoding', 'identity' )
        
        return request

    def _log_request_response( self, request, response ):
        '''
        Send the request and the response to the output manager.
        '''
        method = request.get_method()
        url =  request.get_full_url()
        headers = request.headers
        postData = request.get_data()

        for i in request.unredirected_hdrs.keys():
            headers[ i ] = request.unredirected_hdrs[ i ]
        fr = createFuzzableRequestRaw(method, url, postData, headers)

        if isinstance(response, httpResponse.httpResponse):
            res = response
        else:
            code, msg, hdrs = response.code, response.msg, response.info()
            url = response.geturl()
            body = response.read()
            id = response.id
            # BUGBUG: This is where I create/log the responses that always have 0.2 as the time!
            res = httpResponse.httpResponse( code, body, hdrs, url, url, msg=msg, id=id)
        om.out.logHttp( fr, res )
    
    def http_response(self, request, response):
        response.id = self.inc_counter()
        self._log_request_response( request, response )
        request.id = response.id
        return response

    https_request = http_request
    https_response = http_response

