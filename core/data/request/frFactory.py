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
# used to parse multipart posts
import cgi
# for json
try:
    import extlib.simplejson as json
except:
    import simplejson as json

import core.data.parsers.dpCache as dpCache
import core.data.parsers.urlParser as urlParser
import core.data.parsers.wsdlParser as wsdlParser
import core.data.request.httpPostDataRequest as httpPostDataRequest
import core.data.request.httpQsRequest as httpQsRequest
import core.data.request.wsPostDataRequest as wsPostDataRequest
import core.data.request.jsonPostDataRequest as jsonPostDataRequest
import core.data.request.xmlrpcRequest as xmlrpcRequest
from core.data.dc.cookie import cookie as cookie
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
import core.data.kb.config as cf
from core.data.dc.queryString import queryString

def createFuzzableRequests( httpResponse, request=None, add_self=True ):
    '''
    Generates the fuzzable requests based on an http response instance.
    
    @parameter httpResponse: An httpResponse instance.
    @parameter request: The HTTP request that generated the httpResponse
    @parameter add_self: If I should add the current HTTP request (@parameter request) to the result
    on not.
    
    @return: A list of fuzzable requests.
    '''
    res = []
    
    # query string
    url = httpResponse.getURL()
    QSObject = urlParser.getQueryString( httpResponse.getURI() )
    
    # Headers for all fuzzable requests created here:
    # And add the fuzzable headers to the dict
    headers = {}
    for header_name in cf.cf.getData('fuzzableHeaders' ):
        if header_name not in headers:
            headers[ header_name ] = ''
    
    # Get the cookie!
    cookieObj = _createCookie( httpResponse )
    
    #
    # create the fuzzable request that represents the request object passed as parameter
    #
    if add_self:
        self_headers = {}
        if request:
            self_headers = request.getHeaders()
        for header_name in cf.cf.getData('fuzzableHeaders' ):
            if header_name not in headers:
                self_headers[ header_name ] = ''

        qsr = httpQsRequest.httpQsRequest()
        qsr.setURL( url )
        qsr.setDc( QSObject )
        qsr.setHeaders( self_headers )
        qsr.setCookie( cookieObj )
        res.append( qsr )
    
    # Try to find forms in the document
    form_list = []
    try:
        dp = dpCache.dpc.getDocumentParserFor( httpResponse )
    except w3afException:
        # Failed to find a suitable parser for the document
        pass
    else:
        form_list = dp.getForms()
    
    if not form_list:
        
        # Check if its a wsdl file
        wsdlp = wsdlParser.wsdlParser()
        try:
            wsdlp.setWsdl( httpResponse.getBody() )
        except w3afException:
            pass
        else:
            webServiceList = wsdlp.getMethods()
            if len( webServiceList ) != 0:
                for remoteMethod in webServiceList:
                    wspdr = wsPostDataRequest.wsPostDataRequest()
                    wspdr.setURL( remoteMethod.getLocation() )
                    wspdr.setAction( remoteMethod.getAction() )
                    wspdr.setParameters( remoteMethod.getParameters() )
                    wspdr.setNS( remoteMethod.getNamespace() )
                    wspdr.setMethodName( remoteMethod.getMethodName() )
                    wspdr.setHeaders( headers )
                    res.append( wspdr )     
        
    else:
        # create one httpPostDataRequest for each form variant
        mode = cf.cf.getData('fuzzFormComboValues')
        for form in form_list:
            for variant in form.getVariants(mode):
                if form.getMethod().upper() == 'POST':
                    r = httpPostDataRequest.httpPostDataRequest()
                    r.setMethod(variant.getMethod())
                    r.setFileVariables(form.getFileVariables())
                else:
                    # The default is a GET request
                    r = httpQsRequest.httpQsRequest()
                r.setURL(variant.getAction())
                r.setDc(variant)
                r.setHeaders(headers)
                r.setCookie(cookieObj)
                res.append(r)
    return res

def createFuzzableRequestRaw(method, url, postData, headers):
    '''
    Creates a fuzzable request based on a query sent FROM the browser. This is used in
    plugins like spiderMan.
    
    @parameter method: A string that represents the method ('GET', 'POST', etc)
    @parameter url: A string that represents the URL
    @parameter postData: A string that represents the postdata, if its a GET request, set to None.
    @parameter headers: A dict that holds the headers
    '''
    #
    # Just a query string request ! no postdata
    #
    if not postData:
        qsr = httpQsRequest.httpQsRequest()
        qsr.setURL(url)
        qsr.setMethod(method)
        qsr.setHeaders(headers)
        dc = urlParser.getQueryString(url)
        qsr.setDc(dc)
        return qsr
    #
    # Seems to be something that has post data
    #
    pdr = httpPostDataRequest.httpPostDataRequest()
    pdr.setURL(url)
    pdr.setMethod(method)
    for header_name in headers.keys():
        if header_name.lower() == 'content-length':
            del headers[header_name]
    pdr.setHeaders(headers)
    #
    #   Parse the content
    #   Case #1, multipart form data
    #
    if 'content-type' in headers.keys() and headers['content-type'].startswith('multipart/form-data'):
        tmp, pdict = cgi.parse_header(headers['content-type'])
        try:
            dc = cgi.parse_multipart(StringIO(postData), pdict)
        except:
            om.out.debug('Multipart form data is invalid, the browser sent something wierd.')
        else:
            resultDc = queryString()
            for i in dc.keys():
                resultDc[i] = dc[i]
            # We process multipart requests as x-www-form-urlencoded
            # TODO We need native support of multipart requests!
            headers['content-type'] = 'application/x-www-form-urlencoded'
            pdr.setDc(resultDc)
            pdr.setHeaders(headers)
            return pdr
    #
    #   Case #2, JSON request
    #
    try:
        dc = json.loads(postData)
    except:
        pass
    else:
        # It's json! welcome to the party dude!
        pdr = jsonPostDataRequest.jsonPostDataRequest()
        pdr.setURL(url)
        pdr.setMethod(method)
        pdr.setHeaders(headers)
        pdr.setDc(dc)
        return pdr
    #
    #   Case #3, XMLRPC request
    #
    postDataLower = postData.lower()
    stopWords = [
            '<methodcall>',
            '<methodname>',
            '<params>',
            '</methodcall>',
            '</methodname>',
            '</params>'
            ]
    allStopWords = True
    for word in stopWords:
        if word not in postDataLower:
            allStopWords = False
    if allStopWords:
        xmlrpc_request = xmlrpcRequest.xmlrpcRequest(postData)
        xmlrpc_request.setURL( url )
        xmlrpc_request.setMethod( method )
        xmlrpc_request.setHeaders( headers )
        return xmlrpc_request
    #
    #   Case #4, the "default".
    #
    # NOT a JSON or XMLRPC request!, let's try the simple url encoded post data...
    #
    try:
        dc = urlParser.getQueryString( 'http://w3af/?' + postData )
        pdr.setDc( dc )
    except:
        om.out.debug('Failed to create a data container that can store this data: "' + postData + '".')
    else:
        return pdr

def _createCookie( httpResponse ):
    '''
    Create a cookie object based on a HTTP response.
    '''
    responseHeaders = httpResponse.getHeaders()
    responseCookies = []
    for headerName in responseHeaders:
        if 'cookie' in headerName.lower():
            responseCookies.append( responseHeaders[ headerName ] )
    tmp = ''
    for c in responseCookies:
        tmp += c
    return cookie( tmp )
