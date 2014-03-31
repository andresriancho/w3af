"""
WebServiceRequest.py

Copyright 2006 Andres Riancho

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

"""
import cgi

from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest
from w3af.core.data.dc.headers import Headers


class WebServiceRequest(HTTPPostDataRequest):
    """
    This class represents a fuzzable request for a webservice method call.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, url, action, params,
                 ns, meth_name, headers=Headers()):
        HTTPPostDataRequest.__init__(self, url, headers=headers)
        self._action = action
        self._NS = ns
        self._name = meth_name
        self.set_parameters(params)

    def get_data(self):
        """
        :return: XML with the remote method call

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
        """
        res = '<?xml version="1.0" encoding="UTF-8"?>\n'
        res += '<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema">\n'
        res += '<SOAP-ENV:Body>\n'
        res += '<ns1:' + self.get_methodName(
        ) + ' xmlns:ns1="' + self.get_ns() + '" SOAP-ENC:root="1">\n'
        count = 0
        for param in self.get_parameters():
            count += 1
            res += '<v' + str(count) + ' xsi:type="xsd:' + param.get_type() + '">' + \
                cgi.escape(
                    self._dc[param.get_name()]) + '</v' + str(count) + '>\n'

        res += '</ns1:' + self.get_methodName() + '>\n'
        res += '</SOAP-ENV:Body>\n'
        res += '</SOAP-ENV:Envelope>\n'
        return res

    def get_headers(self):
        """
        web service calls MUST send a header with the action:
            -   SOAPAction: "urn:xmethodsBabelFish#BabelFish"
        """
        self._headers['SOAPAction'] = '"' + self.get_action() + '"'
        self._headers['Content-Type'] = 'text/xml'

        return self._headers

    def get_ns(self):
        return self._NS

    def set_ns(self, ns):
        self._NS = ns

    def get_action(self):
        return self._action

    def set_action(self, a):
        self._action = a

    def get_methodName(self):
        return self._name

    def set_methodName(self, name):
        self._name = name

    def get_parameters(self):
        return self._parameters

    def set_parameters(self, par):
        # Fixed bug #1958368, we have to save this!
        self._parameters = par
        # And now save it so we can fuzz it.
        for param in par:
            self._dc[param.get_name()] = ''

    def __str__(self):
        """
        Return a str representation of this fuzzable request.
        """
        strRes = '[[webservice]] '
        strRes += self._url
        strRes += ' | Method: ' + self._method
        if len(self._dc):
            strRes += ' | Parameters: ('
            for i in self._dc.keys():
                strRes += i + ','
            strRes = strRes[:-1]
            strRes += ')'
        return strRes

    def __repr__(self):
        return '<WS fuzzable request | %s | %s >' % (self.get_method(),
                                                     self.get_uri())
