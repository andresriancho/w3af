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

from __future__ import with_statement
import urllib2
import thread

import core.controllers.outputManager as om
import core.data.request.fuzzableRequest as fuzzableRequest
import core.data.url.httpResponse as httpResponse
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser


class logHandler(urllib2.BaseHandler, urllib2.HTTPDefaultErrorHandler, urllib2.HTTPRedirectHandler):
    """
    Add an unique id attribute to http responses and then log them.
    """
    
    handler_order = urllib2.HTTPErrorProcessor.handler_order -1
    
    def __init__(self):
        self._lock = thread.allocate_lock()
        
        # xUrllib needs access to this method to identify requests with strange errors
        # requests that are returned when the target URL is blacklisted, or some other
        # special cases.
        kb.kb.save('idHandler', 'inc_counter', self.inc_counter )
    
    def inc_counter( self, step=1 ):
        '''
        @return: The next number to use in the request/response ID.
        '''
        # Use a lock to make sure that we don't have problems with different
        # threads that are requesting things to the xUrllib 
        with self._lock:
            c = kb.kb.getData('idHandler', 'counter')
            if c == []:
                kb.kb.save('idHandler', 'counter', 0 )
                c = 0

            c += step
            kb.kb.save('idHandler', 'counter', c)
            return c
            
    def _get_counter( self ):
        '''
        @return: The current counter number to assign as the id for responses.
        '''
        with self._lock:
            c = kb.kb.getData('idHandler', 'counter')
            if c == []:
                kb.kb.save('idHandler', 'counter', 0 )
                c = 0
            return c

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
            
            new_request = urllib2.Request(newurl,
            headers=req.headers,
            origin_req_host=req.get_origin_req_host(),
            unverifiable=True)
            
            return new_request
        else:
            err = urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
            err.id = self.inc_counter()
            raise err
    
    old_http_error_302 = urllib2.HTTPRedirectHandler.http_error_302

    def mod_http_error_302(self, req, fp, code, msg, headers):
        '''
        This is a http_error_302 wrapper to add an id attr to loop errors.
        '''
        id_for_error = self._get_counter()
        try:
            return self.old_http_error_302(req, fp, code, msg, headers)
        except urllib2.HTTPError, e:
            #om.out.debug('The remote web application generated a redirect loop when requesting: ' + \
            #e.geturl() )
            e.id = id_for_error
            raise e
        
    http_error_301 = http_error_303 = http_error_307 = http_error_302 = mod_http_error_302
    
    def http_request(self, request):
        '''
        perform some ugly hacking of request headers and go on...
        '''
        if not request.has_header('Host'):
            request.add_unredirected_header('Host', request.host )
            
        if not request.has_header('Accept-Encoding'):
            request.add_unredirected_header('Accept-Encoding', 'identity' )
        
        return request

    def _log_request_response( self, request, response ):
        '''
        Send the request and the response to the output manager.
        '''
        fr = fuzzableRequest.fuzzableRequest()
        fr.setURI( request.get_full_url() )
        fr.setMethod( request.get_method() )
        
        headers = request.headers
        for i in request.unredirected_hdrs.keys():
            headers[ i ] = request.unredirected_hdrs[ i ]
        fr.setHeaders( headers )
        
        if request.get_data() == None:
            fr.setData( '' )
        else:
            fr.setData( request.get_data() )
        
        if isinstance(response, httpResponse.httpResponse):
            res = response
        else:
            code, msg, hdrs = response.code, response.msg, response.info()
            url = response.geturl()
            body = response.read()
            id = response.id
            res = httpResponse.httpResponse( code, body, hdrs, url, url, msg=msg, id=id)
        om.out.logHttp( fr, res )
    
    def http_response(self, request, response):
        response.id = self.inc_counter()
        self._log_request_response( request, response )
        request.id = response.id
        return response

    https_request = http_request
    https_response = http_response

