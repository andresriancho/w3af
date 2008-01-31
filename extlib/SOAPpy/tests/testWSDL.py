#!/usr/bin/env python

import unittest
import os, re
import sys
sys.path.insert (1, '..')
import SOAPpy

ident = '$Id: testWSDL.py,v 1.2 2003/05/09 12:46:11 warnes Exp $'

# Check for a web proxy definition in environment
try:
   proxy_url=os.environ['http_proxy']
   phost, pport = re.search('http://([^:]+):([0-9]+)', proxy_url).group(1,2)
   http_proxy = "%s:%s" % (phost, pport)
except:
   http_proxy = None



class IntegerArithmenticTestCase(unittest.TestCase):

    def setUp(self):
        self.wsdlstr1 = '''<?xml version="1.0"?>
        <definitions name="TemperatureService" targetNamespace="http://www.xmethods.net/sd/TemperatureService.wsdl"  xmlns:tns="http://www.xmethods.net/sd/TemperatureService.wsdl"   xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns="http://schemas.xmlsoap.org/wsdl/">
                <message name="getTempRequest">
                        <part name="zipcode" type="xsd:string"/>
                </message>
                <message name="getTempResponse">
                        <part name="return" type="xsd:float"/>
                </message>
                <portType name="TemperaturePortType">
                        <operation name="getTemp">
                                <input message="tns:getTempRequest"/>
                                <output message="tns:getTempResponse"/>
                        </operation>
                </portType>
                <binding name="TemperatureBinding" type="tns:TemperaturePortType">
                        <soap:binding style="rpc" transport="http://schemas.xmlsoap.org/soap/http"/>
                        <operation name="getTemp">
                                <soap:operation soapAction=""/>
                                <input>
                                        <soap:body use="encoded" namespace="urn:xmethods-Temperature" encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"/>
                                </input>
                                <output>
                                        <soap:body use="encoded" namespace="urn:xmethods-Temperature" encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"/>
                                </output>
                        </operation>
                </binding>
                <service name="TemperatureService">
                        <documentation>Returns current temperature in a given U.S. zipcode  </documentation>
                        <port name="TemperaturePort" binding="tns:TemperatureBinding">
                                <soap:address location="http://services.xmethods.net:80/soap/servlet/rpcrouter"/>
                        </port>
                </service>
        </definitions>
        '''

    def testParseWsdlString(self):
        '''Parse XMethods TemperatureService wsdl from a string.'''

        wsdl = SOAPpy.WSDL.Proxy(self.wsdlstr1, http_proxy=http_proxy)
        self.assertEquals(len(wsdl.methods), 1)
        method = wsdl.methods.values()[0]
        self.assertEquals(method.methodName, 'getTemp')
        self.assertEquals(method.namespace, 'urn:xmethods-Temperature')
        self.assertEquals(method.location, 
                'http://services.xmethods.net:80/soap/servlet/rpcrouter')

    def testParseWsdlFile(self):
        '''Parse XMethods TemperatureService wsdl from a file.'''

        # figure out path to the test directory
        dir = os.path.abspath('.')
        fname = './TemperatureService.wsdl'

        try:
            f = file(fname)
        except (IOError, OSError):
            self.assert_(0, 'Cound not find wsdl file "%s"' % file)

        wsdl = SOAPpy.WSDL.Proxy(fname, http_proxy=http_proxy)
        self.assertEquals(len(wsdl.methods), 1)
        method = wsdl.methods.values()[0]
        self.assertEquals(method.methodName, 'getTemp')
        self.assertEquals(method.namespace, 'urn:xmethods-Temperature')
        self.assertEquals(method.location, 
                'http://services.xmethods.net:80/soap/servlet/rpcrouter')

    def testParseWsdlUrl(self):
        '''Parse XMethods TemperatureService wsdl from a url.'''

        wsdl = SOAPpy.WSDL.Proxy('http://www.xmethods.net/sd/2001/TemperatureService.wsdl', http_proxy=http_proxy)
        self.assertEquals(len(wsdl.methods), 1)
        method = wsdl.methods.values()[0]
        self.assertEquals(method.methodName, 'getTemp')
        self.assertEquals(method.namespace, 'urn:xmethods-Temperature')
        self.assertEquals(method.location, 
                'http://services.xmethods.net:80/soap/servlet/rpcrouter')

    def testGetTemp(self):
        '''Parse TemperatureService and call getTemp.'''

        zip = '01072'
        proxy = SOAPpy.WSDL.Proxy(self.wsdlstr1, http_proxy=http_proxy)
        temp = proxy.getTemp(zip)
        print 'Temperature at', zip, 'is', temp


if __name__ == '__main__':
    unittest.main()

