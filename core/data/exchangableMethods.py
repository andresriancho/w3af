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

from .request.httpPostDataRequest import httpPostDataRequest
from .request.httpQsRequest import HTTPQSRequest

def isExchangable(self, fuzzableRequest):
    '''
    @parameter mutant: The mutant you want to test if sending using
        querystring or postdata is the same.
    @return: [True|False]
    '''
    if not (isinstance(fuzzableRequest, HTTPQSRequest) or
             isinstance(fuzzableRequest, httpPostDataRequest)) :
        return False
        
    # I get the mutant as it is
    response = self._sendMutant(fuzzableRequest, analyze=False)
    
    if fuzzableRequest.getMethod() == 'GET':
        # I have to create a httpPostDataRequest and set all
        # the parameters to it.
        pdr = httpPostDataRequest(
                          fuzzableRequest.getURL(),
                          headers=fuzzableRequest.getHeaders(),
                          cookie=fuzzableRequest.getCookie(),
                          dc=fuzzableRequest.getDc()
                          )
        response2 = self._sendMutant(pdr, analyze=False)
    
    elif fuzzableRequest.getMethod() == 'POST':
        # I have to create a HTTPQSRequest and set all the parameters to it.
        qsr = HTTPQSRequest(
                    fuzzableRequest.getURL(),
                    headers=fuzzableRequest.getHeaders(),
                    cookie=fuzzableRequest.getCookie()
                    )
        qsr.setDc(fuzzableRequest.getDc())
        response2 = self._sendMutant(qsr, analyze=False)
        
    return response2.getBody() == response.getBody()

