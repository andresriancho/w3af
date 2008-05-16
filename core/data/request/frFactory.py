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
import core.data.parsers.dpCache as dpCache

import core.data.parsers.urlParser as urlParser
import core.data.parsers.wsdlParser as wsdlParser

import core.data.request.httpPostDataRequest as httpPostDataRequest
import core.data.request.httpQsRequest as httpQsRequest
import core.data.request.wsPostDataRequest as wsPostDataRequest
import core.data.request.jsonPostDataRequest as jsonPostDataRequest

from core.data.dc.cookie import cookie as cookie

# used to parse multipart posts
import cgi

# for json
from extlib.jsonpy import json as json

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
import core.data.kb.config as cf

def createFuzzableRequests( httpResponse, addSelf=True ):
    '''
    Generates the fuzzable requests based on an http response instance.
    
    @parameter httpResponse: An httpResponse instance.
    '''
    res = []
    
    # query string
    url = httpResponse.getURL()
    QSObject = urlParser.getQueryString( httpResponse.getURI() )
    
    # Headers
    headers = {}
    for header in cf.cf.getData('fuzzableHeaders' ):
        headers[ header ] = ''
    
    # Get the cookie!
    cookieObj = _createCookie( httpResponse )
    
    # create a httpQsRequest
    qsr = httpQsRequest.httpQsRequest()
    qsr.setURL( url )
    qsr.setDc( QSObject )
    qsr.setHeaders( headers )
    qsr.setCookie( cookieObj )
    if addSelf:
        res.append( qsr )
    
    # forms
    dp = dpCache.dpc.getDocumentParserFor( httpResponse.getBody(), httpResponse.getRedirURI() )
    formList = dp.getForms()
    
    if len( formList ) == 0:
        
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
        # create one httpPostDataRequest for each form
        for form in formList:
            if form.getMethod().upper() == 'GET':
                qsr = httpQsRequest.httpQsRequest()
                qsr.setURL( url )
                qsr.setDc( QSObject )
                qsr.setHeaders( headers )
                qsr.setCookie( cookieObj )
                res.append( qsr )
            elif form.getMethod().upper() == 'POST':
                pdr = httpPostDataRequest.httpPostDataRequest()
                pdr.setURL( form.getAction() )
                pdr.setMethod( form.getMethod() )
                pdr.setFileVariables( form.getFileVariables() )
                pdr.setDc( form )
                pdr.setHeaders( headers )
                pdr.setCookie( cookieObj )
                res.append( pdr )

    return res

def createFuzzableRequestRaw( method, url, postData, headers ):
    '''
    Creates a fuzzable request based on a query sent FROM the browser. This is used in
    plugins like spiderMan.
    
    @parameter method: A string that represents the method ('GET', 'POST', etc)
    @parameter url: A string that represents the URL
    @parameter postData: A string that represents the postdata, if its a GET request, set to None.
    @parameter headers: A dict that holds the headers
    '''
    res = None
    if postData and len( postData ):
        # Seems to be something that has post data
        pdr = httpPostDataRequest.httpPostDataRequest()
        pdr.setURL( url )
        pdr.setMethod( method )
        if 'content-length' in headers.keys():
            headers.pop('content-length')
        pdr.setHeaders( headers )
        
        # Parse the content
        if 'content-Type' in headers.keys() and headers['content-Type'] == 'multipart/form-data':
            try:
                dc = cgi.parse_multipart( postData, headers )
            except:
                om.out.debug('Multipart form data is invalid, the browser sent something wierd.')
            else:
                for i in dc.keys():
                    dc = dc[ i ][0]
                pdr.setDc( dc )
        else:
            # Let's try if this is a json request...
            try:
                dc = json.read( postData )
            except:
                # NOT a JSON request!, let's try the simple url encoded post data...
                try:
                    dc = urlParser.getQueryString( 'http://w3af/?' + postData )
                    pdr.setDc( dc )
                except:
                    om.out.debug('Failed to create a data container that can store this data: "' + postData + '".')
            else:
                # It's json! welcome to the party dude!
                pdr = jsonPostDataRequest.jsonPostDataRequest()
                pdr.setURL( url )
                pdr.setMethod( method )
                pdr.setHeaders( headers )
                pdr.setDc( dc )             
    
        res = pdr
    
    else:
        # Just a query string request ! no postdata
        qsr = httpQsRequest.httpQsRequest()
        qsr.setURL( url )
        qsr.setMethod( method )
        qsr.setHeaders( headers )
        dc = urlParser.getQueryString( url )
        qsr.setDc( dc )         
        res = qsr
        
    return res
    
    
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
