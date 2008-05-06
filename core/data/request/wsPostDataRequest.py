'''
wsPostDataRequest.py

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

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.data.request.httpPostDataRequest import httpPostDataRequest
import core.data.dc.dataContainer as dc
import cgi

class wsPostDataRequest(httpPostDataRequest):
    '''
    This class represents a fuzzable request for a webservice method call. 
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        httpPostDataRequest.__init__(self)
        self._NS = None
        self._name = None
        self._parameters = None
        self._action = None

    def getData( self ):
        '''
        @return: XML with the remote method call

        POST /perl/soaplite.cgi HTTP/1.0
        Host: services.xmethods.net:80
        User-agent: SOAPpy 0.11.3 (pywebsvcs.sf.net)
        Content-type: text/xml; charset="UTF-8"
        Content-length: 561
        SOAPAction: "urn:xmethodsBabelFish#BabelFish"
        
        <?xml version="1.0" encoding="UTF-8"?>
        <SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema">
        <SOAP-ENV:Body>
        <ns1:BabelFish xmlns:ns1="urn:xmethodsBabelFish" SOAP-ENC:root="1">
        <v1 xsi:type="xsd:string">en_fr</v1>
        <v2 xsi:type="xsd:string">Hi Friend!</v2>
        </ns1:BabelFish>
        </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>
        '''
        res = '<?xml version="1.0" encoding="UTF-8"?>\n'
        res += '<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema">\n'
        res += '<SOAP-ENV:Body>\n'
        res += '<ns1:' + self.getMethodName() + ' xmlns:ns1="' + self.getNS() +'" SOAP-ENC:root="1">\n'
        count = 0
        for param in self.getParameters():
            count += 1
            res += '<v' + str(count) +' xsi:type="xsd:'+ param.getType() + '">'+ \
            cgi.escape( self._dc[param.getName()] ) +'</v' + str(count) +'>\n'
            
        res += '</ns1:' + self.getMethodName() + '>\n'
        res += '</SOAP-ENV:Body>\n'
        res += '</SOAP-ENV:Envelope>\n'
        return res
        
    def getHeaders( self ):
        '''
        web service calls MUST send a header with the action:
            -   SOAPAction: "urn:xmethodsBabelFish#BabelFish"
        '''
        self._headers[ 'SOAPAction' ] = '"' + self.getAction() + '"'
        self._headers['Content-Type'] = 'text/xml'
        
        return self._headers
        
    def getNS( self ): return self._NS
    def setNS( self , ns ): self._NS = ns
    
    def getAction( self ): return self._action
    def setAction( self , a ): self._action = a
    
    def getMethodName( self ): return self._name
    def setMethodName( self , name ): self._name = name
    
    def getParameters( self ): return self._parameters
    def setParameters( self, par ):
        # Fixed bug #1958368, we have to save this!
        self._parameters = par
        # And now save it so we can fuzz it.
        for param in par:
            self._dc[ param.getName() ] = ''

    def __str__( self ):
        '''
        Return a str representation of this fuzzable request.
        '''
        strRes = '[[webservice]] '
        strRes += self._url
        strRes += ' | Method: ' + self._method
        if len(self._dc):
            strRes += ' | Parameters: ('
            for i in self._dc.keys():
                strRes += i + ','
            strRes = strRes[: -1]
            strRes += ')'
        return strRes
        
    def __repr__( self ):
        return '<WS fuzzable request | '+ self.getMethod() +' | '+ self.getURI() +' >'
