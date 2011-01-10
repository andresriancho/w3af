import sys
sys.path.insert(1, "..")
from SOAPpy import *

detailed_fault = \
"""
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.microsoft.com/soap/encoding/clr/1.0 http://schemas.xmlsoap.org/soap/encoding/" xmlns:a1="http://schemas.microsoft.com/clr/ns/System.Runtime.Serialization.Formatters">
<SOAP-ENV:Body>
<SOAP-ENV:Fault id="ref-1">

<faultcode>soapenv:Server.generalException</faultcode>
<faultstring>Exception thrown on Server</faultstring>

<detail>
<loginFailureFault href="#id0"/>
<exceptionName xsi:type="xsd:string">...</exceptionName>
</detail>

</SOAP-ENV:Fault>

<multiRef id="id0">
<description xsi:type="xsd:string">Login failure (504):Unknown User</description>
<module xsi:type="xsd:string"> ... </module>
<timestamp xsi:type="xsd:string">...</timestamp>
<faultcode xsi:type="xsd:string"> ...</faultcode>
<parameter xsi:type="xsd:string"> ... </parameter>
</multiRef>

</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
"""

z = parseSOAPRPC(detailed_fault.strip() )
assert(z.__class__==faultType)
assert(z.faultstring=="Exception thrown on Server")
assert(z.detail.loginFailureFault.description=='Login failure (504):Unknown User')
print "Success"
