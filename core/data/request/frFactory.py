'''
frFactory.py

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
from StringIO import StringIO
import cgi
import json

from .httpPostDataRequest import httpPostDataRequest
from .httpQsRequest import HTTPQSRequest
from .jsonPostDataRequest import JSONPostDataRequest
from .wsPostDataRequest import wsPostDataRequest
from .xmlrpcRequest import XMLRPCRequest
from core.controllers.misc.encoding import smart_unicode
from core.controllers.w3afException import w3afException
from core.data.dc.cookie import Cookie
from core.data.dc.queryString import QueryString
from core.data.parsers.urlParser import parse_qs
from core.data.url.HTTPRequest import HTTPRequest
import core.controllers.outputManager as om
import core.data.kb.config as cf
import core.data.parsers.dpCache as dpCache
import core.data.parsers.wsdlParser as wsdlParser


__all__ = ['createFuzzableRequests', 'create_fuzzable_request']


def createFuzzableRequests(resp, request=None, add_self=True):
    '''
    Generates the fuzzable requests based on an http response instance.
    
    @parameter resp: An HTTPResponse instance.
    @parameter request: The HTTP request that generated the resp
    @parameter add_self: If I should add the current HTTP request
        (@parameter request) to the result on not.
    
    @return: A list of fuzzable requests.
    '''
    is_redirect = lambda resp: 300 <= resp.getCode() < 400
    res = []
    
    # Headers for all fuzzable requests created here:
    # And add the fuzzable headers to the dict
    headers = dict((h, '') for h in cf.cf.getData('fuzzableHeaders'))
    req_headers = dict(headers)
    req_headers.update(request and request.getHeaders() or {})
    
    # Get the cookie!
    cookieObj = _create_cookie(resp)
    
    # Create the fuzzable request that represents the request object
    # passed as parameter
    if add_self:
        qsr = HTTPQSRequest(
                    resp.getURI(),
                    headers=req_headers,
                    cookie=cookieObj
                    )
        res.append(qsr)
    
    # If response was a 30X (i.e. a redirect) then include the
    # corresponding fuzzable request. 
    if is_redirect(resp):
        redir_headers = resp.getLowerCaseHeaders()
        location = redir_headers.get('location') or \
                        redir_headers.get('uri', '')
        if location:
            location = smart_unicode(location, encoding=resp.charset)
            try:
                absolute_location = resp.getURL().urlJoin(location)
            except ValueError:
                msg = 'The application sent a 30x redirect "Location:" that'
                msg += ' w3af failed to correctly parse as an URL, the header'
                msg += ' value was: "%s"'
                om.out.debug( msg % location )
            else:
                qsr = HTTPQSRequest(
                    absolute_location,
                    headers=req_headers,
                    cookie=cookieObj
                    )
                res.append(qsr)
    
    # Try to find forms in the document
    try:
        dp = dpCache.dpc.getDocumentParserFor(resp)
    except w3afException:
        # Failed to find a suitable parser for the document
        form_list = []
    else:
        form_list = dp.getForms()
    
    if not form_list:
        # Check if its a wsdl file
        wsdlp = wsdlParser.wsdlParser()
        try:
            wsdlp.setWsdl(resp.getBody())
        except w3afException:
            pass
        else:
            for rem_meth in wsdlp.getMethods():
                wspdr = wsPostDataRequest(
                                  rem_meth.getLocation(),
                                  rem_meth.getAction(),
                                  rem_meth.getParameters(),
                                  rem_meth.getNamespace(),
                                  rem_meth.getMethodName(),
                                  headers
                                  )
                res.append(wspdr)
    else:
        # Create one httpPostDataRequest for each form variant
        mode = cf.cf.getData('fuzzFormComboValues')
        for form in form_list:
            for variant in form.getVariants(mode):
                if form.getMethod().upper() == 'POST':
                    r = httpPostDataRequest(
                                        variant.getAction(),
                                        variant.getMethod(),
                                        headers,
                                        cookieObj,
                                        variant,
                                        form.getFileVariables()
                                        )
                else:
                    # The default is a GET request
                    r = HTTPQSRequest(
                                  variant.getAction(),
                                  headers=headers,
                                  cookie=cookieObj
                                  )
                    r.setDc(variant)
                
                res.append(r)
    return res

XMLRPC_WORDS = ('<methodcall>', '<methodname>', '<params>',
                '</methodcall>', '</methodname>', '</params>')
def create_fuzzable_request(req_url, method='GET', post_data='',
                            add_headers=None):
    '''
    Creates a fuzzable request based on the input parameters.

    @param req_url: Either a url_object that represents the URL or a
        HTTPRequest instance. If the latter is the case the `method` and
        `post_data` values are taken from the HTTPRequest object as well
        as the values in `add_headers` will be merged with the request's
        headers.
    @param method: A string that represents the method ('GET', 'POST', etc)
    @param post_data: A string that represents the postdata.
    @param add_headers: A dict that holds the headers. If `req_url` is a
        request then this dict will be merged with the request's headers.
    '''
    if isinstance(req_url, HTTPRequest):
        url = req_url.url_object
        post_data = str(req_url.get_data() or '')
        method = req_url.get_method()
        headers = dict(req_url.headers)
        headers.update(add_headers or {})
    else:
        url = req_url
        headers = add_headers or {}

    # Just a query string request! No postdata
    if not post_data:
        req = HTTPQSRequest(url, method, headers)
 
    else: # Seems to be something that has post data
        data = {}
        conttype = ''
        for hname in headers.keys(): # '.keys()' is just fine. Don't
            hnamelow = hname.lower() # remove it.
            if hnamelow == 'content-length':
                del headers[hname]
            elif hnamelow == 'content-type':
                conttype = headers.get('content-type', '').lower()
        
        # Case #1 - JSON request
        try:
            data = json.loads(post_data)
        except:
            pass

        if data:
            req = JSONPostDataRequest(url, method, headers, dc=data)
        
        # Case #2 - XMLRPC request
        elif all(map(lambda stop: stop in post_data.lower(), XMLRPC_WORDS)):
            req = XMLRPCRequest(post_data, url, method, headers)

        else:
            # Case #3 - multipart form data - prepare data container
            if conttype.startswith('multipart/form-data'):
                pdict = cgi.parse_header(conttype)[1]
                try:
                    dc = cgi.parse_multipart(StringIO(post_data), pdict)
                except:
                    om.out.debug('Multipart form data is invalid, the browser '
                                 'sent something weird.')
                else:
                    data = QueryString()
                    data.update(dc)
                    # We process multipart requests as x-www-form-urlencoded
                    # TODO: We need native support of multipart requests!
                    headers['content-type'] = \
                                        'application/x-www-form-urlencoded'
            
            # Case #4 - a typical post request
            else:
                try:
                    data = parse_qs(post_data)
                except:
                    om.out.debug('Failed to create a data container that '
                                 'can store this data: "' + post_data + '".')
            # Finally create request
            req = httpPostDataRequest(url, method, headers, dc=data)
    return req

def _create_cookie(httpResponse):
    '''
    Create a cookie object based on a HTTP response.
    '''
    cookies = []
        
    # Get data from RESPONSE
    responseHeaders = httpResponse.getHeaders()
    
    for hname, hvalue in responseHeaders.items():
        if 'cookie' in hname.lower():
            cookies.append(hvalue)
                
    cookie_inst = Cookie(''.join(cookies))
    
    #
    # delete everything that the browsers usually keep to themselves, since
    # this cookie object is the one we're going to send to the wire
    #
    for key in ['path', 'expires', 'domain', 'max-age']:
        try:
            del cookie_inst[key]
        except:
            pass
    
    return cookie_inst 

