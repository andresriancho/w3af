'''
exchangableMethods.py

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
from .request.HTTPPostDataRequest import HTTPPostDataRequest
from .request.HTTPQsRequest import HTTPQSRequest


def isExchangable(uri_opener, freq):
    '''
    @param uri_opener: The URI opener to use in order to verify if methods can
                       be exchanged for this fuzzable request.
                       
    @param freq: The fuzzable request you want to test if sending using
                 querystring or postdata is the same.
                   
    @return: [True|False]
    '''
    if not (isinstance(freq, HTTPQSRequest) or
             isinstance(freq, HTTPPostDataRequest)) :
        return False
        
    response = uri_opener.send_mutant(freq)
    
    if freq.get_method() == 'GET':
        # I have to create a HTTPPostDataRequest and set all
        # the parameters to it.
        pdr = HTTPPostDataRequest(
                          freq.getURL(),
                          headers=freq.getHeaders(),
                          cookie=freq.getCookie(),
                          dc=freq.getDc()
                          )
        response2 = uri_opener.send_mutant(pdr)
    
    elif freq.get_method() == 'POST':
        # I have to create a HTTPQSRequest and set all the parameters to it.
        qsr = HTTPQSRequest(
                    freq.getURL(),
                    headers=freq.getHeaders(),
                    cookie=freq.getCookie()
                    )
        qsr.setDc(freq.getDc())
        response2 = uri_opener.send_mutant(qsr)
        
    return response2.getBody() == response.getBody()

