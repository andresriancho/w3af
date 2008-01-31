#!/usr/bin/env python

ident = '$Id: speedTest.py,v 1.4 2003/05/21 14:52:37 warnes Exp $'

import time
import sys
sys.path.insert(1, "..")

x='''<SOAP-ENV:Envelope
      xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
      xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance"
      xmlns:xsd="http://www.w3.org/1999/XMLSchema">
      <SOAP-ENV:Body>
         <ns1:getRate xmlns:ns1="urn:demo1:exchange"  SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <country1 xsi:type="xsd:string">USA</country1>
            <country2 xsi:type="xsd:string">japan</country2>
         </ns1:getRate>
      </SOAP-ENV:Body>
   </SOAP-ENV:Envelope>'''

x2='''<SOAP-ENV:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.microsoft.com/soap/encoding/clr/1.0 http://schemas.xmlsoap.org/soap/encoding/" xmlns:i3="http://soapinterop.org/xsd" xmlns:i2="http://soapinterop.org/">
<SOAP-ENV:Body>
<i2:echoStructArray id="ref-1">
<return href="#ref-4"/>
</i2:echoStructArray>
<SOAP-ENC:Array id="ref-4" SOAP-ENC:arrayType="i3:SOAPStruct[3]">
<item href="#ref-5"/>
<item href="#ref-6"/>
<item href="#ref-7"/>
</SOAP-ENC:Array>
<i3:SOAPStruct id="ref-5">
<varString xsi:type="xsd:string">West Virginia</varString>
<varInt xsi:type="xsd:int">-546</varInt>
<varFloat xsi:type="xsd:float">-5.398</varFloat>
</i3:SOAPStruct>
<i3:SOAPStruct id="ref-6">
<varString xsi:type="xsd:string">New Mexico</varString>
<varInt xsi:type="xsd:int">-641</varInt>
<varFloat xsi:type="xsd:float">-9.351</varFloat>
</i3:SOAPStruct>
<i3:SOAPStruct id="ref-7">
<varString xsi:type="xsd:string">Missouri</varString>
<varInt xsi:type="xsd:int">-819</varInt>
<varFloat xsi:type="xsd:float">1.495</varFloat>
</i3:SOAPStruct>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''

# Import in function, because for some reason they slow each other
# down in same namespace ???
def SOAPParse(inxml):
    from SOAPpy import parseSOAPRPC
    t=  time.time()
    parseSOAPRPC(inxml)
    return time.time()-t

def SAXParse(inxml):
    import xml.sax
    y = xml.sax.handler.ContentHandler()
    t=  time.time()
    xml.sax.parseString(inxml,y)
    return time.time()-t

def DOMParse(inxml):
    import xml.dom.minidom
    t=  time.time()
    xml.dom.minidom.parseString(inxml)
    return time.time()-t

# Wierd but the SAX parser runs really slow the first time.
# Probably got to load a c module or something
SAXParse(x)
print
print "Simple XML"
print "SAX Parse, no marshalling   ", SAXParse(x)
print "SOAP Parse, and marshalling ", SOAPParse(x)
print "DOM Parse, no marshalling   ", DOMParse(x)
print
print "Complex XML (references)"
print "SAX Parse, no marshalling   ", SAXParse(x2)
print "SOAP Parse, and marshalling ", SOAPParse(x2)
print "DOM Parse, no marshalling   ", DOMParse(x2)
