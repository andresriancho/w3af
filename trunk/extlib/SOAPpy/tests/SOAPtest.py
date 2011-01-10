#!/usr/bin/env python

################################################################################
#
# A bunch of regression type tests for the builder and parser.
#
################################################################################

ident = '$Id: SOAPtest.py,v 1.19 2004/04/01 13:25:46 warnes Exp $'

import urllib
import sys
import unittest
import re

sys.path.insert(1, "..")
from SOAPpy import *
config=Config
config.strict_range=1


# run these tests with this variable set both to 1 and 0
config.simplify_objects=0

# as borrowed from jake.soapware.org for float compares.
def nearlyeq(a, b, prec = 1e-7):
    return abs(a - b) <= abs(a) * prec

# helper
def negfloat(x):
    return float(x) * -1.0

class Book(structType):
    def __init__(self):
        self.title = "Title of a book"
        structType.__init__(self)
        
class Person(structType):
    def __init__(self):
        self.age = "49"
        self.height = "5.5"
        structType.__init__(self)

class Result(structType):
    def __init__(self):
        structType.__init__(self, name = 'Result')
        self.Book = Book()
        self.Person = Person()

class one:
    def __init__(self):
        self.str = "one"
        
class two:
    def __init__(self):
        self.str = "two"
        
class three:
    def __init__(self):
        self.str = "three"

ws = ' \t\r\n'
N = None
                   
class SOAPTestCase(unittest.TestCase):
    # big message
    def notestBigMessage(self):
        x=[]
        for y in string.lowercase:
            x.append(y*999999)
        buildSOAP(x)
        
    # test arrayType
    def testArrayType(self):
        x = structType( {"name":"widg1","quantity":200,
                              "price":decimalType(45.99),
                              "_typename":"LineItem"})
        y = buildSOAP([x, x])
        # could be parsed using an XML parser?
        self.failUnless(string.find(y, "LineItem")>-1)
    
    # test arguments ordering
    def testOrdering(self):
        x = buildSOAP(method="newCustomer", namespace="urn:customer", \
                      kw={"name":"foo1", "address":"bar"}, \
                      config=SOAPConfig(argsOrdering={"newCustomer":("address", "name")}))
        # could be parsed using an XML parser?
        self.failUnless(string.find(x, "<address ")<string.find(x, "<name "))
        x = buildSOAP(method="newCustomer", namespace="urn:customer", \
                      kw={"name":"foo1", "address":"bar"}, \
                      config=SOAPConfig(argsOrdering={"newCustomer":("name", "address")}))
        # could be parsed using an XML parser?
        self.failUnless(string.find(x, "<address ")>string.find(x, "<name "))

    # test struct
    def testStructIn(self):
        x = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<SomeMethod>
<Result>
<Book>
   <title>My Life and Work</title>
</Book>
<Person>
   <name>Henry Ford</name>
   <age> 49 </age>
   <height> 5.5 </height>
</Person>
</Result>
</SomeMethod>
</soap:Body>
</soap:Envelope>
'''
        # parse rules
        pr = {'SomeMethod':
            {'Result':
                    {'Book':   {'title':(NS.XSD, "string")},
                     'Person': {'age':(NS.XSD, "int"),
                     'height':negfloat}
                }
            }
        }
        y = parseSOAPRPC(x, rules=pr)
        if config.simplify_objects:
            self.assertEquals(y['Result']['Person']['age'], 49);
            self.assertEquals(y['Result']['Person']['height'], -5.5);
        else:
            self.assertEquals(y.Result.Person.age, 49);
            self.assertEquals(y.Result.Person.height, -5.5);

    # Try the reverse
    def testStructOut(self):
        x = buildSOAP(Result())
        
    def testIntFloat(self):
        x='''<SOAP-ENV:Envelope
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    SOAP-ENV:encodingStyle="http://schemas.microsoft.com/soap/encoding/clr/1.0
    http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:i3="http://soapinterop.org/xsd" xmlns:i2="http://soapinterop.org/">
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
            <varFloat xsi:type="xsd:float">1.375</varFloat>
        </i3:SOAPStruct>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''
        y = parseSOAPRPC(x)
        if(config.simplify_objects):
            self.assertEquals(y['return'][0]['varString'], "West Virginia")
            self.assertEquals(y['return'][1]['varInt'], -641)
            self.assertEquals(y['return'][2]['varFloat'], 1.375)
        else:
            self.assertEquals(getattr(y,"return")[0].varString, "West Virginia")
            self.assertEquals(getattr(y,"return")[1].varInt, -641)
            self.assertEquals(getattr(y,"return")[2].varFloat, 1.375)

    def testArray1(self):
        x='''<SOAP-ENV:Envelope
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
    SOAP-ENV:encodingStyle="http://schemas.microsoft.com/soap/encoding/clr/1.0
    http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:i3="http://soapinterop.org/xsd" xmlns:i2="http://soapinterop.org/">
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
            <xsd:string>West Virginia</xsd:string>
            <xsd:int>-546</xsd:int>
            <xsd:float>-5.398</xsd:float>
        </i3:SOAPStruct>
        <i3:SOAPStruct id="ref-6">
            <xsd:string>New Mexico</xsd:string>
            <xsd:int>-641</xsd:int>
            <xsd:float>-9.351</xsd:float>
        </i3:SOAPStruct>
        <i3:SOAPStruct id="ref-7">
            <xsd:string>Missouri</xsd:string>
            <xsd:int>-819</xsd:int>
            <xsd:float>1.375</xsd:float>
        </i3:SOAPStruct>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''
        y = parseSOAPRPC(x)
        if(config.simplify_objects):
            self.assertEquals(y["return"][0]['string'], "West Virginia")
            self.assertEquals(y["return"][1]['int'], -641)
            self.assertEquals(y["return"][2]['float'], 1.375)
        else:
            self.assertEquals(getattr(y,"return")[0].string, "West Virginia")
            self.assertEquals(getattr(y,"return")[1].int, -641)
            self.assertEquals(getattr(y,"return")[2].float, 1.375)

    def testUTF8Encoding1(self):
        x = '''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsd2="http://www.w3.org/2000/10/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:xsi2="http://www.w3.org/2000/10/XMLSchema-instance">
<ns0:echoStringArrayResponse xmlns:ns0="http://soapinterop.org/">
<return2 href="#id3"/>
</ns0:echoStringArrayResponse>
<a id="id0" xmlns:ns0="http://soapinterop.org/" xsi2:type="xsd:string" xsi:type="xsd:string"></a>
<a id="id1" xmlns:ns0="http://soapinterop.org/" xsi2:type="xsd:string" xsi:type="xsd:string">Hello</a>
<a id="id2" xmlns:ns0="http://soapinterop.org/" xsi2:type="xsd:string" xsi:type="xsd:string">\'&lt;&amp;&gt;&quot;</a>
<return2 SOAP-ENC:arrayType="xsd:string[3]" id="id3" xmlns:ns0="http://soapinterop.org/">
<a href="#id0"/>
<a href="#id1"/>
<a href="#id2"/>
</return2>
</SOAP-ENV:Body></SOAP-ENV:Envelope>'''
        y = parseSOAPRPC(x)
        if config.simplify_objects:
            self.assertEquals(y['return2'][1], "Hello")
        else:
            self.assertEquals(y.return2[1], "Hello")
            
    def testUTF8Encoding2(self):
        x = '''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
<ns0:echoStringArrayResponse xmlns:ns0="http://soapinterop.org/">
<a xsi:type="xsd:string"></a>
<a xsi:type="xsd:string">Hello</a>
<a xsi:type="xsd:string">\'&lt;&amp;&gt;&quot;</a>
<b xsi:type="xsd:string">Goodbye</b>
</ns0:echoStringArrayResponse>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''
        y = parseSOAPRPC(x)
        self.assertEquals(type(y.a), type([]))
        self.assertEquals(type(y.b), type(''))
        self.assertEquals(type(y._getItemAsList('a')), type([]))
        self.assertEquals(type(y._getItemAsList('b')), type([]))
        self.assertEquals(y.b, 'Goodbye')
        self.assertEquals(y.a, ['', 'Hello', '\'<&>"'])
        self.assertEquals(y._getItemAsList('b'), ['Goodbye'])
        self.assertEquals(y._getItemAsList('c'), [])
        self.assertEquals(y._getItemAsList('c', 'hello'), 'hello')

    def testUTF8Encoding2(self):
        x = '''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Body
    SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:xsd="http://www.w3.org/1999/XMLSchema"
    xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
<a1 SOAP-ENC:root="1">Hello</a1>
<a2 SOAP-ENC:root="0" id="id">\'&lt;&amp;&gt;&quot;</a2>
<a3>Goodbye</a3>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''
        y = parseSOAP(x)
        self.assertEquals(y.a1, 'Hello')
        self.assertEquals(y.a3, 'Goodbye')
        self.failIf(hasattr(y, 'a2'))

    def testUTF8Encoding3(self):
        x = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<SomeMethod>
<Result>
<Book>
   <title>My Life and Work</title>
   <author href="#Person-1"/>
</Book>
<Person id="Person-1">
   <name>Henry Ford</name>
   <address href="#Address-2"/>
</Person>
<Address id="Address-2">
   <email>mailto:henryford@hotmail.com</email>
   <web>http://www.henryford.com</web>
   <pers href="#Person-1"/>
</Address>
</Result>
</SomeMethod>
</soap:Body>
</soap:Envelope>
'''
        y = parseSOAPRPC(x)
        if config.simplify_objects:
            self.assertEquals(y['Result']['Book']['author']['name'], "Henry Ford")
            self.assertEquals(y['Result']['Book']['author']['address']['web'], "http://www.henryford.com")
            self.assertEquals(y['Result']['Book']['author']['address']['pers']['name'], "Henry Ford")
        else:
            self.assertEquals(y.Result.Book.author.name, "Henry Ford")
            self.assertEquals(y.Result.Book.author.address.web, "http://www.henryford.com")
            self.assertEquals(y.Result.Book.author.address.pers.name, "Henry Ford")
        
    # ref example
    def testRef(self):
        x = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<echoFloatArrayResponse xmlns="http://soapinterop.org/">
<Return href="#i1" xmlns="" />
</echoFloatArrayResponse>
<soapenc:Array id="i1" soapenc:arrayType="xsd:float[4]">
<Item>0</Item>
<Item>1</Item>
<Item>-1</Item>
<Item>3853.33325</Item>
</soapenc:Array>
</soap:Body>
</soap:Envelope>
'''
        y = parseSOAPRPC(x)
        if config.simplify_objects:
            self.assertEquals(y['Return'][0], 0)
            self.assertEquals(y['Return'][1], 1)
            self.assertEquals(y['Return'][2], -1)
            self.failUnless(nearlyeq(y['Return'][3], 3853.33325))
        else:
            self.assertEquals(y.Return[0], 0)
            self.assertEquals(y.Return[1], 1)
            self.assertEquals(y.Return[2], -1)
            self.failUnless(nearlyeq(y.Return[3], 3853.33325))

    # Make sure passing in our own bodyType works.
    def testBodyType(self):
        a = [23, 42]
        b = bodyType()
        b.a = b.b = a

        x = buildSOAP(b)
        y = parseSOAP(x)

        self.assertEquals(id(y.a), id(y.b))
        self.assertEquals(y.a, a)
        self.assertEquals(y.b, a)

    # Test Envelope versioning (see section 4.1.2 of http://www.w3.org/TR/SOAP).
    def testEnvelopeVersioning(self):
        xml = '''<SOAP-ENV:Envelope
    SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
    xmlns:xsd="http://www.w3.org/1999/XMLSchema"
    xmlns:SOAP-ENV="http://new/envelope/version/"
    xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance"
    xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/">
    <SOAP-ENV:Body>
        <_1 xsi:type="xsd:int" SOAP-ENC:root="1">1</_1>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''

        try:
            parseSOAP(xml)
        except Exception, e:
            self.failUnless(isinstance(e, faultType))
            self.assertEquals(e.faultcode, '%s:VersionMismatch' % NS.ENV_T)
            self.failIf(hasattr(e, 'detail'))

    # Big terrible ordered data with attributes test.
    def testBigOrderedData(self):
        data = '''<?xml version="1.0" encoding="UTF-8" ?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
<Body>
<replyBlock generic="1.0" attrib1="false" attrib2='hello'>
<itemList>
<mainItem mainattrib1='uno'>
<name>first_main_item</name>
<description>whatever etc.</description>
<infoList>
<itemInfo a1='123' a2='abc'>
<name>unoItem1</name>
</itemInfo>
<itemInfo a1='456' a2='def'>
<name>unoItem2</name>
</itemInfo>
<itemInfo a1='789' a2='ghi'>
<name>unoItem3</name>
</itemInfo>
</infoList>
</mainItem>
<mainItem mainattrib1='dos'>
<name>second_main_item</name>
<description>whatever etc.</description>
<infoList>
<itemInfo a1='3123' a2='3abc'>
<name>dosItem1</name>
</itemInfo>
<itemInfo a1='3456' a2='3def'>
<name>dosItem2</name>
</itemInfo>
<itemInfo a1='3789' a2='3ghi'>
<name>dosItem3</name>
</itemInfo>
</infoList>
</mainItem>
</itemList>
<itemList>
<mainItem mainattrib1='single'>
<name>single_main_item</name>
<description>whatever etc.</description>
<infoList>
<itemInfo a1='666' a2='xxx'>
<name>singleItem1</name>
</itemInfo>
</infoList>
</mainItem>
</itemList>
</replyBlock>
</Body>
</Envelope>'''

        x = parseSOAP(data)
        # print ".>",x.replyBlock.itemList._ns
        y = buildSOAP(x)

    def testEnvelope1(self):        
        my_xml2 = '''
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<SOAP-ENV:Header>
<t:Transaction xmlns:t="some-URI" SOAP-ENV:mustUnderstand="1">
5
</t:Transaction>
</SOAP-ENV:Header>
   <SOAP-ENV:Body>
       <m:GetLastTradePriceResponse xmlns:m="Some-URI">
            <PriceAndVolume>
                <LastTradePrice>
                    34.5
                </LastTradePrice>
                <DayVolume>
                    10000
                </DayVolume>
            </PriceAndVolume>
       </m:GetLastTradePriceResponse>
   </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        (x,h) = parseSOAPRPC(my_xml2,header=1)

    def testEnvelope2(self):
        x ='''
<V:Envelope
        xmlns:V="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:C="http://schemas.xmlsoap.org/soap/encoding/"
        xmlns:i="http://www.w3.org/1999/XMLSchema-instance"
        xmlns:d="http://www.w3.org/1999/XMLSchema"
        V:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<V:Body>
<m:echoStructArray
        xmlns:m="urn:xmethodsInterop">
<inputStructArray
        i:type="C:Array"
        C:arrayType="ns3:SOAPStruct[0]"
        xmlns:ns3="http://soapinterop.org/xsd"/>
</m:echoStructArray>
</V:Body>
</V:Envelope>'''
        x = parseSOAPRPC(x)        

    def testEnvelope3(self):
        x = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Body>
<m:echoStringResponse xmlns:m="http://soapinterop.org/">
<Result name="fred">hello</Result>
</m:echoStringResponse>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        x, a = parseSOAPRPC(x, attrs = 1) 
        if config.simplify_objects:
            self.assertEquals(a[id(x['Result'])][(None, 'name')], 'fred')
        else:
            self.assertEquals(a[id(x.Result)][(None, 'name')], 'fred')

    def testParseException(self):
        x='''<SOAP-ENV:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.microsoft.com/soap/encoding/clr/1.0 http://schemas.xmlsoap.org/soap/encoding/" xmlns:a1="http://schemas.microsoft.com/clr/ns/System.Runtime.Serialization.Formatters">
<SOAP-ENV:Body>
<SOAP-ENV:Fault id="ref-1">
<faultcode id="ref-2">SOAP-ENV:Server</faultcode>
<faultstring id="ref-3">Exception thrown on Server</faultstring>
<detail xsi:type="a1:ServerFault">

<exceptionType id="ref-4">System.Runtime.Serialization.SerializationException, mscorlib, Version=1.0.2411.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</exceptionType>

<message id="ref-5">Soap Parser Error System.Runtime.Serialization.SerializationException: Parse Error, xsd type not valid: Array
   at System.Runtime.Serialization.Formatters.Soap.SoapHandler.ProcessGetType(String value, String xmlKey)
   at System.Runtime.Serialization.Formatters.Soap.SoapHandler.ProcessType(ParseRecord pr, ParseRecord objectPr)
   at System.Runtime.Serialization.Formatters.Soap.SoapHandler.ProcessAttributes(ParseRecord pr, ParseRecord objectPr)
   at System.Runtime.Serialization.Formatters.Soap.SoapHandler.StartElement(String prefix, String name, String urn)
   at System.XML.XmlParser.ParseElement()
   at System.XML.XmlParser.ParseTag()
   at System.XML.XmlParser.Parse()
   at System.XML.XmlParser.Parse0()
   at System.XML.XmlParser.Run()</message>

<stackTrace id="ref-6">   at System.Runtime.Serialization.Formatters.Soap.SoapHandler.Error(IXmlProcessor p, Exception ex)
   at System.XML.XmlParser.Run()
   at System.Runtime.Serialization.Formatters.Soap.SoapParser.Run()
   at System.Runtime.Serialization.Formatters.Soap.ObjectReader.Deserialize(HeaderHandler handler, ISerParser serParser)
   at System.Runtime.Serialization.Formatters.Soap.SoapFormatter.Deserialize(Stream serializationStream, HeaderHandler handler)
   at System.Runtime.Remoting.Channels.CoreChannel.DeserializeMessage(String mimeType, Stream xstm, Boolean methodRequest, IMessage msg, Header[] h)
   at System.Runtime.Remoting.Channels.SoapServerFormatterSink.ProcessMessage(IServerChannelSinkStack sinkStack, ITransportHeaders requestHeaders, Stream requestStream, IMessage&#38; msg, ITransportHeaders&#38; responseHeaders, Stream&#38; responseStream)</stackTrace>
</detail>

</SOAP-ENV:Fault>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''

        z = parseSOAPRPC(x)
        self.assertEquals(z.__class__,faultType)
        self.assertEquals(z.faultstring, "Exception thrown on Server")

            
    def testFlatEnvelope(self):
        x = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Body><m:echoStringResponse xmlns:m="http://soapinterop.org/"><Result></Result></m:echoStringResponse></SOAP-ENV:Body></SOAP-ENV:Envelope>
'''
        z = parseSOAPRPC(x)
        if config.simplify_objects:
            self.assertEquals(type(z['Result']), type(''))
        else:
            self.assertEquals(type(z.Result), type(''))

    def testNumericArray(self):
        x = [1,2,3,4,5]
        y = buildSOAP(x)
        z = parseSOAPRPC(y)
        self.assertEquals(x, z)

    def testStringArray(self):
        x = ["cayce", "asd", "buy"]
        y = buildSOAP(x)
        z = parseSOAPRPC(y)
        self.assertEquals(x, z)

    def testStringArray1(self):
        x = arrayType(['a', 'b', 'c'])
        y = buildSOAP(x)
        z = parseSOAP(y)
        if config.simplify_objects:        
            self.assertEquals(z.v1._elemsname, 'item')
            self.assertEquals(z.v1, x)
        else:
            self.assertEquals(z['v1']['_elemsname'], 'item')
            self.assertEquals(z['v1'], x)

    def testStringArray2(self):
        x = arrayType(['d', 'e', 'f'], elemsname = 'elementals')
        y = buildSOAP(x)
        z = parseSOAP(y)
        if config.simplify_objects:        
            self.assertEquals(z.v1._elemsname, 'elementals')
            self.assertEquals(z.v1, x)
        else:
            self.assertEquals(z['v1']['_elemsname'], 'elementals')
            self.assertEquals(z['v1'], x)

    def testInt1(self):
        my_xml = '''
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
  <SOAP-ENV:Body>
    <m:getStateName xmlns:m="http://www.soapware.org/">
      <statenum xsi:type="xsd:int">41</statenum>
    </m:getStateName>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        s = parseSOAPRPC(my_xml)
        if config.simplify_objects:
            self.assertEquals(s['statenum'], 41)
            self.assertEquals(type(s['statenum']), type(0))
        else:
            self.assertEquals(s.statenum, 41)
            self.assertEquals(type(s.statenum), type(0))

    def testInt2(self):
        my_xml_ns = '''
<XSOAP-ENV:Envelope XSOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:XSOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:XSOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:Xxsd="http://www.w3.org/1999/XMLSchema" xmlns:Xxsi="http://www.w3.org/1999/XMLSchema-instance">
  <XSOAP-ENV:Body>
    <m:getStateName xmlns:m="http://www.soapware.org/">
      <statenum Xxsi:type="Xxsd:int">41</statenum>
    </m:getStateName>
  </XSOAP-ENV:Body>
</XSOAP-ENV:Envelope>
'''
        s = parseSOAPRPC(my_xml_ns)
        if config.simplify_objects:
            self.assertEquals(s['statenum'], 41, "NS one failed")
            self.assertEquals(type(s['statenum']), type(0))
        else:
            self.assertEquals(s.statenum, 41, "NS one failed")
            self.assertEquals(type(s.statenum), type(0))

    def testPriceAndVolume(self):
        my_xml2 = '''
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<SOAP-ENV:Header>
<t:Transaction xmlns:t="some-URI" SOAP-ENV:mustUnderstand="1">
5
</t:Transaction>
</SOAP-ENV:Header>
   <SOAP-ENV:Body>
       <m:GetLastTradePriceResponse xmlns:m="Some-URI">
            <PriceAndVolume>
                <LastTradePrice>
                    34.5
                </LastTradePrice>
                <DayVolume>
                    10000
                </DayVolume>
            </PriceAndVolume>
       </m:GetLastTradePriceResponse>
   </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        s = parseSOAPRPC(my_xml2)
        if config.simplify_objects:
            self.assertEquals(s['PriceAndVolume']['LastTradePrice'].strip(), "34.5")
            self.assertEquals(s['PriceAndVolume']['DayVolume'].strip(), "10000")
        else:
            self.assertEquals(s.PriceAndVolume.LastTradePrice.strip(), "34.5")
            self.assertEquals(s.PriceAndVolume.DayVolume.strip(), "10000")

    def testInt3(self):
        my_xml3 = '''
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
   <SOAP-ENV:Body>
   <Bounds>
   <param>
   <lowerBound xsi:type="xsd:int"> 18 </lowerBound>
   <upperBound xsi:type="xsd:int"> 139</upperBound>
   </param>
   </Bounds>
   </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        s = parseSOAPRPC(my_xml3)

        if config.simplify_objects:
            self.assertEquals(s['param']['lowerBound'], 18)
            self.assertEquals(s['param']['upperBound'], 139)
        else:
            self.assertEquals(s.param.lowerBound, 18)
            self.assertEquals(s.param.upperBound, 139)

    def testBoolean(self):
        my_xml4 = '''
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
   <SOAP-ENV:Body>
   <Bounds>
<param SOAP-ENC:arrayType="xsd:ur-type[4]" xsi:type="SOAP-ENC:Array"><item xsi:type="xsd:int">12</item>
   <item xsi:type="xsd:string">Egypt</item>
   <item xsi:type="xsd:boolean">0</item>
   <item xsi:type="xsd:int">-31</item>
   </param>
   <param1 xsi:null="1"></param1>
   <param2 xsi:null="true"></param2>
   <param3 xsi:type="xsd:int" xsi:null="false">7</param3>
   </Bounds>
   </SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        s = parseSOAPRPC(my_xml4)
        if config.simplify_objects:
            self.assertEquals(s['param'][0], 12)
            self.assertEquals(s['param'][1], "Egypt")
            self.assertEquals(s['param'][2], 0)
            self.assertEquals(s['param'][3], -31)
            self.assertEquals(s['param1'], None)
            self.assertEquals(s['param2'], None)
            self.assertEquals(s['param3'], 7)
        else:
            self.assertEquals(s.param[0], 12)
            self.assertEquals(s.param[1], "Egypt")
            self.assertEquals(s.param[2], 0)
            self.assertEquals(s.param[3], -31)
            self.assertEquals(s.param1, None)
            self.assertEquals(s.param2, None)
            self.assertEquals(s.param3, 7)

    def testFault(self):
        my_xml5 = '''
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
   <SOAP-ENV:Body>
      <SOAP-ENV:Fault>
         <faultcode>SOAP-ENV:Client</faultcode>
         <faultstring>Cant call getStateName because there are too many parameters.</faultstring>
         </SOAP-ENV:Fault>
      </SOAP-ENV:Body>
   </SOAP-ENV:Envelope>
'''
        s = parseSOAPRPC(my_xml5)
        self.assertEquals(s.__class__, faultType)
        self.assertEquals(s.faultcode, "SOAP-ENV:Client")

    def testArray2(self):
        my_xml6 = '''
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
<SOAP-ENV:Body>
<h SOAP-ENC:arrayType="xsd:ur-type[6]" xsi:type="SOAP-ENC:Array">
<item xsi:type="xsd:int">5</item>
<item xsi:type="xsd:int">3</item>
<item xsi:type="xsd:int">2</item>
<item xsi:type="xsd:string">monkey</item>
<item xsi:type="xsd:string">cay</item>
<item>
<cat xsi:type="xsd:string">hello</cat>
<ferret SOAP-ENC:arrayType="xsd:ur-type[6]" xsi:type="SOAP-ENC:Array">
<item xsi:type="xsd:int">5</item>
<item xsi:type="xsd:int">4</item>
<item xsi:type="xsd:int">3</item>
<item xsi:type="xsd:int">2</item>
<item xsi:type="xsd:int">1</item>
<item>
<cow xsi:type="xsd:string">moose</cow>
</item>
</ferret>
<monkey xsi:type="xsd:int">5</monkey>
</item>
</h>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        q = parseSOAPRPC(my_xml6)
        self.assertEquals(q[0], 5)
        self.assertEquals(q[1], 3)
        self.assertEquals(q[2], 2)
        self.assertEquals(q[3], 'monkey')
        self.assertEquals(q[4], 'cay')
        x = q[5]
        if config.simplify_objects:
            self.assertEquals(x['monkey'], 5)
            self.assertEquals(x['cat'], "hello")
            self.assertEquals(x['ferret'][0], 5)
            self.assertEquals(x['ferret'][3], 2)
            self.assertEquals(x['ferret'][5]['cow'], "moose")
        else:
            self.assertEquals(x.monkey, 5)
            self.assertEquals(x.cat, "hello")
            self.assertEquals(x.ferret[0], 5)
            self.assertEquals(x.ferret[3], 2)
            self.assertEquals(x.ferret[5].cow, "moose")

    def testArray3(self):
        x = arrayType([5,4,3,21], "spam")
        y = buildSOAP(x)
        z = parseSOAPRPC(y)
        self.assertEquals(x, z)

    # test struct
    def testStruct(self):
        x = structType(name = "eggs")
        x.test = 5
        y = buildSOAP(x)
        z = parseSOAPRPC(y)
        if config.simplify_objects:
            self.assertEquals( x['test'], z['test'] )
        else:
            self.assertEquals( x.test, z.test )

    # test faults
    def testFault1(self):
        x = faultType("ServerError","Howdy",[5,4,3,2,1])
        y = buildSOAP(x)

        z = parseSOAPRPC(y)
        self.assertEquals( x.faultcode ,  z.faultcode)
        self.assertEquals( x.faultstring ,  z.faultstring)
        self.assertEquals( x.detail ,  z.detail)
        
    # Test the recursion
    def testRecursion(self):
        o = one()
        t = two()
        o.t = t
        t.o = o
        tre = three()
        tre.o = o
        tre.t = t
        x = buildSOAP(tre)
        y = parseSOAPRPC(x)
        if config.simplify_objects:
            self.assertEquals( y['t']['o']['t']['o']['t']['o']['t']['str'] ,  "two")
        else:
            self.assertEquals( y.t.o.t.o.t.o.t.str ,  "two")

    # Test the recursion with structs
    def testRecursionWithStructs(self):
        o = structType("one")
        t = structType("two")
        o.t = t
        o.str = "one"
        t.o = o
        t.str = "two"
        tre = structType("three")
        tre.o = o
        tre.t = t
        tre.str = "three"
        x = buildSOAP(tre)
        y = parseSOAPRPC(x)
        if config.simplify_objects:
            self.assertEquals( y['t']['o']['t']['o']['t']['o']['t']['str'] ,  "two")
        else:
            self.assertEquals( y.t.o.t.o.t.o.t.str ,  "two")

    def testAmp(self):
        m = "Test Message <tag> & </tag>"
        x = structType("test")
        x.msg = m
        y = buildSOAP(x)
        z = parseSOAPRPC(y)
        if config.simplify_objects:
            self.assertEquals( m ,  z['msg'])
        else:
            self.assertEquals( m ,  z.msg)

    def testInt4(self):
        my_xml7 = '''
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
<SOAP-ENV:Body>
<Bounds>
<param>
<lowerBound xsi:type="xsd:int"> 18 </lowerBound>
<upperBound xsi:type="xsd:int"> 139</upperBound>
</param>
</Bounds>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>
'''
        x = parseSOAPRPC(my_xml7)
        y = buildSOAP(x)
        
    # Does buildSOAP require a valid encoding?
    def testBuildSOAPEncoding(self):
        try:
            x = buildSOAP('hello', encoding = 'gleck')
        except LookupError, e:
            if str (e)[0:16] != 'unknown encoding': raise
            x = None
        except:
            print "Got unexpected exception: %s %s" % tuple (sys.exc_info ()[0:2])
            x = ''
        self.assertEquals( x ,  None)

    # Does SOAPProxy require a valid encoding?
    def testSOAPProxyEncoding(self):
        try:
            x = SOAPProxy('', encoding = 'gleck')
        except LookupError, e:
            if str (e)[0:16] != 'unknown encoding': raise
            x = None
        except:
            print "Got unexpected exception: %s %s" % tuple (sys.exc_info ()[0:2])
            x = ''
        self.assertEquals( x ,  None)

    # Does SOAPServer require a valid encoding?
    def testSOAPServerEncoding(self):
        try:
            x = SOAPServer(('localhost', 0), encoding = 'gleck')
        except LookupError, e:
            if str (e)[0:16] != 'unknown encoding': raise
            x = None
        except:
            print "Got unexpected exception: %s %s" % tuple (sys.exc_info ()[0:2])
            x = ''
        self.assertEquals( x ,  None)

    def testEncodings(self):
        encodings = ('US-ASCII', 'ISO-8859-1', 'UTF-8', 'UTF-16')

        tests = ('A', u'\u0041')
        for t in tests:
            for i in range (len (encodings)):
                x = buildSOAP (t, encoding = encodings[i])
                y = parseSOAPRPC (x)
                self.assertEquals( y ,  t)

        tests = (u'\u00a1',)
        for t in tests:
            for i in range (len (encodings)):
                try:
                    x = buildSOAP (t, encoding = encodings[i])
                except:
                    if i > 0: raise
                    continue
                y = parseSOAPRPC (x)
                self.assertEquals( y ,  t)

        tests = (u'\u01a1', u'\u2342')
        for t in tests:
            for i in range (len (encodings)):
                try:
                    x = buildSOAP (t, encoding = encodings[i])
                except:
                    if i > 1: raise
                    continue
                y = parseSOAPRPC (x)
                self.assertEquals( y ,  t)

    def build_xml(self, schema, type, value, attrs = ''):
        return '''<?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope
        SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
        xmlns:xsd="%(schema)s"
        xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
        <SOAP-ENV:Body>
            <_1 xsi:type="xsd:%(type)s"%(attrs)s>%(value)s</_1>
        </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>''' % {'schema': schema, 'type': type, 'value': value,
        'attrs': attrs}

    # Make sure the various limits are checked when parsing
    def testIntegerLimits(self):
        for t, l in SOAPParser.intlimits.items():
            try:
                parseSOAP(xml % (NS.XSD, t, 'hello'))
                raise AssertionError, "parsed %s of 'hello' without error" % t
            except AssertionError:
                raise
            except:
                pass

            if l[1] != None:
                try:
                    parseSOAP(self.build_xml(NS.XSD, t, l[1] - 1))
                    raise AssertionError, "parsed %s of %s without error" % \
                        (t, l[1] - 1)
                except AssertionError:
                    raise
                except UnderflowError:
                    pass

            if l[2] != None:
                try:
                    parseSOAP(self.build_xml(NS.XSD, t, l[2] + 1))
                    raise AssertionError, "parsed %s of %s without error" % \
                        (t, l[2] + 1)
                except AssertionError:
                    raise
                except OverflowError:
                    pass

    # Make sure the various limits are checked when parsing
    # Next, floats. Note that chances are good this won't work in any non-Unix Pythons.
    def testFloatLimits(self):
        for i in \
            (
                ('float', '-3.402823466391E+38'),
                ('float',  '3.402823466391E+38'),
                ('float', '3.5e+38'),
                ('float', '6.9e-46'),
                ('double', '-1.7976931348623159E+308'),
                ('double',  '1.7976931348623159E+308'),
                ('double', '1.8e308'),
                ('double', '2.4e-324'),
            ):
            try:
                parseSOAP(self.build_xml(NS.XSD, i[0], i[1]))
                
                # Hide this error for now, cause it is a bug in python 2.0 and 2.1
                #if not (sys.version_info[0] == 2 and sys.version_info[1] <= 2) \
                #       and i[1]=='1.7976931348623159E+308':
                raise AssertionError, "parsed %s of %s without error" % i
            except AssertionError:
                raise
            except (UnderflowError, OverflowError):
                pass

    # Make sure we can't instantiate the base classes
    def testCannotInstantiateBaseClasses(self):
        for t in (anyType, NOTATIONType):
            try:
                x = t()
                raise AssertionError, "instantiated %s directly" % repr(t)
            except:
                pass

    # Try everything that requires initial data without any.
    def testMustBeInitialized(self):
        for t in (CDATAType, ENTITIESType, ENTITYType, IDType, IDREFType,
            IDREFSType, NCNameType, NMTOKENType, NMTOKENSType, NOTATIONType,
            NameType, QNameType, anyURIType, base64Type, base64BinaryType,
            binaryType, booleanType, byteType, decimalType, doubleType,
            durationType, floatType, hexBinaryType, intType, integerType,
            languageType, longType, negative_IntegerType, negativeIntegerType,
            non_Negative_IntegerType, non_Positive_IntegerType,
            nonNegativeIntegerType, nonPositiveIntegerType, normalizedStringType,
            positive_IntegerType, positiveIntegerType, shortType, stringType,
            timeDurationType, tokenType, unsignedByteType, unsignedIntType,
            unsignedLongType, unsignedShortType, untypedType, uriType,
            uriReferenceType):
            try:
                t()
                raise AssertionError, "instantiated a %s with no value" % t.__name__
            except AssertionError:
                raise
            except:
                pass


    def testInstantiations(self):
        # string, ENTITY, ID, IDREF, language, Name, NCName,
        # NMTOKEN, QName, untypedType
        for t in (stringType, ENTITYType, IDType, IDREFType,
                  languageType, NameType, NCNameType, NMTOKENType,
                  QNameType, untypedType):
            # First some things that shouldn't be taken as the current type

            test = (10, (), [], {})
            for i in test:
                try:
                    t(i)
                    
                    raise AssertionError, \
                        "instantiated a %s with a bad type (%s)" % \
                            (repr(t), repr(type(i)))
                except AssertionError:
                    raise
                except:
                    pass

            # Now some things that should

            for i in ('hello', u'goodbye'):
                x = t(i)
                d = x._marshalData()

                if d != i:
                    raise AssertionError, "expected %s, got %s" % (i, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != i:
                    raise AssertionError, "expected %s, got %s" % (i, z)
                
        # ENTITIES, IDREFS, NMTOKENS
        for t in (ENTITIESType, IDREFSType, NMTOKENSType):
            # First some things that shouldn't be taken as the current type

            test = ({}, lambda x: x, ((),), ([],), [{}], [()])

            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a %s with a bad type (%s)" % \
                            repr(t), repr(type(i))
                except AssertionError:
                    raise
                except:
                    pass

            # Now some things that should

            for i in ('hello', (), [], ('hello', 'goodbye'), ['aloha', 'guten_tag']):
                x = t(i)
                d = x._marshalData()

                if type(i) in (type(()), type([])):
                    j = list(i)
                else:
                    j = [i]
                k = ' '.join(j)

                if d != k:
                    raise AssertionError, "expected %s, got %s" % (k, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != j:
                    raise AssertionError, "expected %s, got %s" % (repr(j), repr(z))

        # uri, uriReference, anyURI
        for t in (uriType, uriReferenceType, anyURIType):
            # First some things that shouldn't be taken as the current type

            test = (10, (), [], {})
            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a %s with a bad type (%s)" % \
                            t.__name__, repr(type(i))
                except AssertionError:
                    raise
                except:
                    pass

            # Now some things that should

            for i in ('hello', u'goodbye', '!@#$%^&*()-_=+[{]}\|;:\'",<.>/?`~'):
                x = t(i)
                d = x._marshalData()

                j = urllib.quote(i)

                if d != j:
                    raise AssertionError, "expected %s, got %s" % (j, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != i:
                    raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # token First some things that shouldn't be valid because of type
        test = (42, 3.14, (), [], {})
        t = tokenType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad type (%s)" % (t.__name__, repr(i))
            except AssertionError:
                raise
            except AttributeError:
                pass

        # Now some things that shouldn't be valid because of content

        test = (' hello', 'hello ', 'hel\nlo', 'hel\tlo', 'hel  lo', ' \n    \t ')

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                      "instantiated a %s with a bad value (%s)" % (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should be valid

        for i in ('', 'hello', u'hello'):
            x = t(i)
            d = x._marshalData()

            if d != i:
                raise AssertionError, "expected %s, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i and i != '':
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        #### CDATA, normalizedString

        for t in (CDATAType, normalizedStringType):
            # First some things that shouldn't be valid because of type

            test = (42, 3.14, (), [], {})

            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a %s with a bad type (%s)" % \
                            (t.__name__, repr(i))
                except AssertionError:
                    raise
                except AttributeError:
                    pass

            # Now some things that shouldn't be valid because of content

            test = ('hel\nlo', 'hel\rlo', 'hel\tlo', '\n\r\t')

            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a %s with a bad value (%s)" % \
                            (t.__name__, repr(i))
                except AssertionError:
                    raise
                except ValueError:
                    pass

            # Now some things that should be valid

            for i in ('', 'hello', u'hello', 'hel lo'):
                x = t(i)
                d = x._marshalData()

                if d != i:
                    raise AssertionError, "expected %s, got %s" % (i, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != i and i != '':
                    raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        #### boolean

        # First some things that shouldn't be valid

        test = (10, 'hello', (), [], {})
        t = booleanType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % (t.__name__, repr(i))
            except AssertionError:
                raise
            except:
                pass

        # Now some things that should

        for i in ((0, 'false'), ('false', 'false'), (1, 'true'),
            ('true', 'true'), (0.0, 'false'), (1.0, 'true')):
            x = t(i[0])
            d = x._marshalData()

            if d != i[1]:
                raise AssertionError, "%s: expected %s, got %s" % (i[0], i[1], d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            j = ('false', 'true')[z]

            if j != i[1]:
                raise AssertionError, "%s: expected %s, got %s" % \
                    (i[0], repr(i[1]), repr(j))

        # Now test parsing, both valid and invalid

        test = (('10', None), ('hello', None), ('false', 0), ('FALSE', 0),
            (ws + 'false' + ws, 0), (ws + '0' + ws, 0),
            ('0', 0), ('true', 1), ('TRUE', 1), ('1', 1),
            (ws + 'true' + ws, 1), (ws + '1' + ws, 1))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != None:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

        # Can we give it a name and no type?

        #print
        x = t(1, name = 'George', typed = 0)
        #print "x=",x
        y = buildSOAP(x)
        #print "y=",y
        z = parseSOAP(y)
        #print "z=",z

        test = 'true'
        if z.George != test:
            raise AssertionError, "expected %s, got %s" % (repr(test), repr(z))

        # How about some attributes, set in various and sundry manners?

        x = t(1, attrs = {'nonamespaceURI': 1})
        x._setAttrs({(None, 'NonenamespaceURI'): 2,
            ('http://some/namespace', 'namespaceURIattr1'): 3})
        x._setAttr(('http://some/other/namespace', 'namespaceURIattr2'), 4)

        self.assertEquals( x._getAttr('nonamespaceURI') ,  1)
        self.assertEquals( x._getAttr('NonenamespaceURI') ,  2)
        self.assertEquals( x._getAttr(('http://some/namespace',
                                       'namespaceURIattr1')) ,  3)
        self.assertEquals( x._getAttr(('http://some/other/namespace',
                                       'namespaceURIattr2')) ,  4)
        self.assertEquals( x._getAttr('non-extant attr') ,  None)

        y = buildSOAP(x)
        z = parseSOAPRPC(y)

        self.assertEquals( z ,  1)

        #### decimal

        # First some things that shouldn't be valid

        test = ('hello', (), [], {})
        t = decimalType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                      "instantiated a %s with a bad type (%s)" % \
                      (t.__name__, repr(type(i)))
            except AssertionError:
                raise
            except:
                pass

        # Now some things that should

        for i in (10, 3.14, 23L):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %f, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', None), ('1.2.3', None), ('10', 10), ('10.', 10),
            ('.1', .1), ('.1000000', .1), (ws + '10.4' + ws, 10.4))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != None:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

        #### float

        # First some things that shouldn't be valid

        test = ('hello', (), [], {}, -3.402823466391E+38, 3.402823466391E+38)
        t = floatType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                    (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (10, 3.14, 23L, -3.4028234663852886E+38, 3.4028234663852886E+38):
            x = t(i)
            d = x._marshalData()

            if not nearlyeq(float(d), i):
                raise AssertionError, "expected %f, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if not nearlyeq(z, i):
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', None), ('1.2.3', None), ('10', 10), ('10.', 10),
            ('.1', .1), ('.1000000', .1), (ws + '10.4' + ws, 10.4),
            ('-3.402823466391E+38', None), ('3.402823466391E+38', None),
            ('-3.4028234663852886E+38', -3.4028234663852886E+38),
            ('3.4028234663852886E+38', 3.4028234663852886E+38))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if abs(z - i[1]) > 1e-6:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != None:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

        #### double

        # First some things that shouldn't be valid

        test = ('hello', (), [], {},
            -1.7976931348623159E+308, 1.7976931348623159E+308)
        t = doubleType

        for i in test:
            try:
                t(i)
                # Hide this error for now, cause it is a bug in python 2.0 and 2.1
                if not (sys.version_info[0] == 2 and  sys.version_info[1] <= 2
                        and i==1.7976931348623159E+308):
                    raise AssertionError, \
                          "instantiated a double with a bad value (%s)" % repr(i)
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (10, 3.14, 23L, -1.79769313486E+308, 1.79769313486E+308):
            x = t(i)
            d = x._marshalData()

            if not nearlyeq(float(d), i):
                raise AssertionError, "expected %s, got %s" % (i, str(x))

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if not nearlyeq(z, i):
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', None), ('1.2.3', None), ('10', 10), ('10.', 10),
            ('.1', .1), ('.1000000', .1), (ws + '10.4' + ws, 10.4),
            ('-1.7976931348623159E+308', None), ('1.7976931348623158E+308', None),
            ('-1.79769313486E+308', -1.79769313486E+308),
            ('1.79769313486E+308', 1.79769313486E+308))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if abs(z - i[1]) > 1e-6:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != None:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

        #### hexBinary

        x = ''
        for i in range(256):
            x += chr(i)
        test = ('', x, 'hello')
        t = hexBinaryType

        l = []
        for i in test:
            l.append(hexBinaryType(i))

        x = buildSOAP(l)
        y = parseSOAPRPC(x)

        for i in range(len(test)):
            if test[i] != y[i]:
                raise AssertionError, "@ %d expected '%s', got '%s'" % \
                    (i, test[i], y[i])

        # Now test parsing, both valid and invalid

        test = (('hello', None), ('6163 747A65726F', None), ('6163747A65726', None),
            ('6163747A65726F', 'actzero'), (ws + '6163747A65726F' + ws, 'actzero'))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != None:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

        #### base64Binary and base64

        s = ''
        for i in range(256):
            s += chr(i)

        for t in (base64BinaryType, base64Type):
            # First some things that shouldn't be valid

            test = ((), [], {}, lambda x: x)

            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a %s with a bad value (%s)" % \
                            (t.__name__, repr(i))
                except AssertionError:
                    raise
                except AttributeError:
                    pass

            # Now some things that should

            test = ('', s, u'hello')

            l = []
            for i in test:
                l.append(t(i))

            x = buildSOAP(l)
            y = parseSOAPRPC(x)

            for i in range(len(test)):
                if test[i] != y[i]:
                    raise AssertionError, "@ %d expected '%s', got '%s'" % \
                        (i, test[i], y[i])

            # Now test parsing, both valid and invalid

            test = (('hello', None), ('YWN0emVybw=', None),
                ('YWN 0emVybw==', 'actzero'), ('YWN0emVybw==', 'actzero'),
                (ws + 'YWN0emVybw==' + ws, 'actzero'))

            for i in test:
                try:
                    z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                    if z != i[1]:
                        raise AssertionError, "%s: expected %s, got %s" % \
                            (i[0], i[1], repr(z))
                except AssertionError:
                    raise
                except:
                    if i[1] != None:
                        raise AssertionError, \
                            "parsing %s as %s threw exception %s:%s" % \
                            (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

        #### binary (uses s from above)

        # First some check invalid encodings

        try:
            x = binaryType('hello', encoding = 'yellow')
            raise AssertionError, "created binary with invalid encoding"
        except AssertionError:
            raise
        except:
            pass

        for t in ('hex', 'base64'):
            # First some things that shouldn't be valid

            test = ((), [], {}, lambda x: x)

            for i in test:
                try:
                    binaryType(i, encoding = t)
                    raise AssertionError, \
                        "instantiated a %s binary with a bad value (%s)" % \
                            (e, repr(i))
                except AssertionError:
                    raise
                except AttributeError:
                    pass

            # Now some things that should

            test = ('', s, u'hello')

            l = []
            for i in test:
                l.append(binaryType(i, encoding = t))

            x = buildSOAP(l)
            y = parseSOAPRPC(x)

            for i in range(len(test)):
                if test[i] != y[i]:
                    raise AssertionError, "@ %d expected '%s', got '%s'" % \
                        (i, test[i], y[i])

            # Now test parsing, both valid and invalid

            if t == 'hex':
                test = (('hello', None), ('6163 747A65726F', None),
                    ('6163747A65726', None), ('6163747A65726F', 'actzero'),
                    (ws + '6163747A65726F' + ws, 'actzero'))
            else:
                test = (('hello', None), ('YWN0emVybw=', None),
                    ('YWN 0emVybw==', 'actzero'), ('YWN0emVybw==', 'actzero'),
                    (ws + 'YWN0emVybw==' + ws, 'actzero'))

            for i in test:
                try:
                    z = parseSOAPRPC(self.build_xml(NS.XSD, 'binary', i[0],
                        ' encoding="%s"' % t))

                    if z != i[1]:
                        raise AssertionError, "%s: expected %s, got %s" % \
                            (i[0], i[1], repr(z))
                except AssertionError:
                    raise
                except:
                    if i[1] != None:
                        raise AssertionError, \
                            "parsing %s as %s threw exception %s:%s" % \
                            (i[0], t, sys.exc_info()[0], sys.exc_info()[1])

            # Finally try an Array of binaries (with references!)

            test = ('', s, u'hello')

            l = []
            for i in test:
                l.append(binaryType(i, encoding = t))

            l.append(l[1])
            x = buildSOAP(l)
            y = parseSOAPRPC(x)

            for i in range(len(test)):
                if test[i] != y[i]:
                    raise AssertionError, "@ %d expected '%s', got '%s'" % \
                        (i, test[i], y[i])

            # Make sure the references worked

            self.assertEquals( id(y[1]) ,  id(y[3]))
    
    def badTest(self, t, data):
        for i in data:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except:
                pass

    def goodTest(self, t, data):
        for i in data:
            x = t(i[0])
            d = x._marshalData()

            if d != i[1]:
                raise AssertionError, "%s(%s): expected %s, got %s" % \
                    (t.__name__, repr(i[0]), i[1], d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i[2]:
                raise AssertionError, "%s(%s): expected %s, got %s" % \
                    (t.__name__, repr(i[0]), repr(i[2]), repr(z))

    def parseTest(self, t, data):
        for i in data:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4],
                    i[0]))

                if z != i[1]:
                    raise AssertionError, "%s(%s): expected %s, got %s" % \
                        (t.__name__, repr(i[0]), i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def allTests(self, t, baddata, gooddata, parsedata):
        self.badTest(t, baddata)
        self.goodTest(t, gooddata)
        self.parseTest(t, parsedata)

    # duration and timeDuration
    def testTimeDuration(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (-10, -10),
                (-10, 0, -10),
                (10.5, 10.5),
                (0, 10.5, 0, 10.5, 0),
                (1, 2, 3, 4, 5, 6, 7),
                (1, 2, 'hello', 4, 5, 6),
                (1, 2, 3.5, 4, 5, 6),
            )
        gooddata = \
            (
                (0, 'PT0S', (N, N, N, N, N, 0.0,)),
                ((), 'PT0S', (N, N, N, N, N, 0.0,)),
                ([], 'PT0S', (N, N, N, N, N, 0.0,)),
                ((0.5,), 'PT0.5S', (N, N, N, N, N, 0.5,)),
                (10L, 'PT10S', (N, N, N, N, N, 10.0,)),
                (-10, '-PT10S', (N, N, N, N, N, -10.0,)),
                (10.5, 'PT10.5S', (N, N, N, N, N, 10.5,)),
                ((10L, 20), 'PT10M20S', (N, N, N, N, 10, 20.0)),
                ((-10, 20), '-PT10M20S', (N, N, N, N, -10, 20.0)),
                ((10, 0), 'PT10M', (N, N, N, N, 10, N)),
                ((10, 0, 0), 'PT10H', (N, N, N, 10, N, N)),
                ((10, 0L, 0, 0), 'P10D', (N, N, 10, N, N, N)),
                ((10, 0, 0, 0, 0), 'P10M', (N, 10, N, N, N, N)),
                ((10, 0, 0, 0L, 0, 0), 'P10Y', (10, N, N, N, N, N)),
                ((-10, 0, 0, 0, 0, 0), '-P10Y', (-10, N, N, N, N, N)),
                ((10, 0, 0, 0, 0, 20L), 'P10YT20S', (10, N, N, N, N, 20.0,)),
                ((1, 2, 3, 4, 5, 6.75), 'P1Y2M3DT4H5M6.75S',
                    (1, 2, 3, 4, 5, 6.75)),
                ((-1, 2, 3, 4, 5, 6.75), '-P1Y2M3DT4H5M6.75S',
                    (-1, 2, 3, 4, 5, 6.75)),
                ((1, 2, 3, 10, 30, 0), 'P1Y2M3DT10H30M',
                    (1, 2, 3, 10, 30, N)),
                ((1e6, 2e6, 3e6, 4e6, 5e6, 6.7e6),
                    'P1000000Y2000000M3000000DT4000000H5000000M6700000S',
                    (1e6, 2e6, 3e6, 4e6, 5e6, 6.7e6)),
                ((1347, 0, N, 0, 0), 'P1347M', (N, 1347, N, N, N, N)),
                ((-1347, 0, 0, 0, N), '-P1347M', (N, -1347, N, N, N, N)),
                ((1e15, 0, 0, 0, 0), 'P1000000000000000M',
                    (N, 1000000000000000L, N, N, N, N)),
                ((-1e15, 0, 0, 0, 0), '-P1000000000000000M',
                    (N, -1000000000000000L, N, N, N, N)),
                ((1000000000000000L, 0, 0, 0, 0), 'P1000000000000000M',
                    (N, 1000000000000000L, N, N, N, N)),
                ((-1000000000000000L, 0, 0, 0, 0), '-P1000000000000000M',
                    (N, -1000000000000000L, N, N, N, N)),
            )
        parsedata = (
                ('hello', N),
                ('P T0S', N),
                ('P10.5Y10.5M', N),
                ('P1Y2MT', N),
                ('PT0S', (N, N, N, N, N, 0,)),
                ('P10Y', (10, N, N, N, N, N)),
                (ws + 'P10M' + ws, (N, 10, N, N, N, N)),
                ('P0Y1347M', (0, 1347, N, N, N, N)),
                ('P0Y1347M0D', (0, 1347, 0, N, N, N)),
                ('P0MT0M', (N, 0, N, N, 0, N)),
            )

        for t in (durationType, timeDurationType):
            self.allTests(t, baddata, gooddata, parsedata)

    # dateTime, timeInstant, and timePeriod
    def testTimePeriod(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (1, 2, 3, 4, 5),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (1, 2, 3, 4, 5, 'hello'),
                (1, 2.5, 3, 4, 5, 6),
                (1, 0, 3, 4, 5, 6),
                (1, 13, 3, 4, 5, 6),
                (1, 1, 0, 4, 5, 6),
                (1, 1, 32, 4, 5, 6),
                (1, 2, 29, 4, 5, 6),
                (0, 2, 30, 4, 5, 6),
                (100, 2, 29, 4, 5, 6),
                (1, 2, 3, -1, 5, 6),
                (1, 2, 3, 24, 5, 6),
                (1, 2, 3, 4, -1, 6),
                (1, 2, 3, 4, 60, 6),
                (1, 2, 3, 4, 5, -1),
                (1, 2, 3, 4, 5, 61),
                (1, 3, 32, 4, 5, 6),
                (1, 4, 31, 4, 5, 6),
                (1, 5, 32, 4, 5, 6),
                (1, 6, 31, 4, 5, 6),
                (1, 7, 32, 4, 5, 6),
                (1, 8, 32, 4, 5, 6),
                (1, 9, 31, 4, 5, 6),
                (1, 10, 32, 4, 5, 6),
                (1, 11, 31, 4, 5, 6),
                (1, 12, 32, 4, 5, 6),
            )
        gooddata = \
            (
                (1L, '1970-01-01T00:00:01Z', (1970, 1, 1, 0, 0, 1.0)),
                (1.5, '1970-01-01T00:00:01.5Z', (1970, 1, 1, 0, 0, 1.5)),
                ((-1, 2, 3, 4, 5, 6), '-0001-02-03T04:05:06Z',
                    (-1, 2, 3, 4, 5, 6.0)),
                ((1, 2, 3, 4, 5, 6), '0001-02-03T04:05:06Z',
                    (1, 2, 3, 4, 5, 6.0)),
                ((10, 2, 3, 4, 5, 6), '0010-02-03T04:05:06Z',
                    (10, 2, 3, 4, 5, 6.0)),
                ((100, 2, 3, 4, 5, 6), '0100-02-03T04:05:06Z',
                    (100, 2, 3, 4, 5, 6.0)),
                ((1970, 2, 3, 4, 5, 6), '1970-02-03T04:05:06Z',
                    (1970, 2, 3, 4, 5, 6.0)),
                ((-1970, 2, 3, 4, 5, 6), '-1970-02-03T04:05:06Z',
                    (-1970, 2, 3, 4, 5, 6.0)),
                ((1970L, 2.0, 3.0, 4L, 5L, 6.875), '1970-02-03T04:05:06.875Z',
                    (1970, 2, 3, 4, 5, 6.875)),
                ((11990, 1, 2, 3, 4L, 5.25, 0, 0, 0),
                    '11990-01-02T03:04:05.25Z',
                    (11990, 1, 2, 3, 4, 5.25)),
                ((1e15, 1, 2, 3, 4L, 5.25, 0, 0, 0),
                    '1000000000000000-01-02T03:04:05.25Z',
                    (1e15, 1, 2, 3, 4, 5.25)),
                ((-1e15, 1, 2, 3, 4L, 5.25, 0, 0, 0),
                    '-1000000000000000-01-02T03:04:05.25Z',
                    (-1e15, 1, 2, 3, 4, 5.25)),
                ((1000000000000000L, 1, 2, 3, 4L, 5.25, 0, 0, 0),
                    '1000000000000000-01-02T03:04:05.25Z',
                    (1e15, 1, 2, 3, 4, 5.25)),
                ((-1000000000000000L, 1, 2, 3, 4L, 5.25, 0, 0, 0),
                    '-1000000000000000-01-02T03:04:05.25Z',
                    (-1e15, 1, 2, 3, 4, 5.25)),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('1970 -01 -01T00:00:01Z', N),
                ('0001-02-03t07:08:23Z', N),

                # Invalid ranges
                ('2001-00-03T07:08:23Z', N),
                ('2001-13-03T07:08:23Z', N),
                ('2001-02-00T07:08:23Z', N),
                ('2001-02-29T07:08:23Z', N),
                ('2000-02-30T07:08:23Z', N),
                ('1900-02-29T07:08:23Z', N),
                ('2001-02-03T24:08:23Z', N),
                ('2001-02-03T04:60:23Z', N),
                ('2001-02-03T04:05:61Z', N),
                ('2001-01-32T04:05:06Z', N),
                ('2001-03-32T04:05:06Z', N),
                ('2001-04-31T04:05:06Z', N),
                ('2001-05-32T04:05:06Z', N),
                ('2001-06-31T04:05:06Z', N),
                ('2001-07-32T04:05:06Z', N),
                ('2001-08-32T04:05:06Z', N),
                ('2001-09-31T04:05:06Z', N),
                ('2001-10-32T04:05:06Z', N),
                ('2001-11-31T04:05:06Z', N),
                ('2001-12-32T04:05:06Z', N),

                # Whitespace
                (ws + '1970-01-01T00:00:00Z' + ws, (1970, 1, 1, 0, 0, 0)),

                # No timezones
                ('11971-02-03T04:05:06.125', (11971, 2, 3, 4, 5, 6.125)),
                ('1971-02-03T04:05:06.125', (1971, 2, 3, 4, 5, 6.125)),
                ('-1971-02-03T04:05:06.125', (-1971, 2, 3, 4, 5, 6.125)),

                # Non-zulu
                ('11971-02-03T04:05:06.125-07:08', (11971, 2, 3, 11, 13, 6.125)),
                ('11971-02-03T04:05:06.125+07:08', (11971, 2, 2, 20, 57, 6.125)),
                ('-11971-02-03T04:05:06.125-07:08', (-11971, 2, 3, 11, 13, 6.125)),
                ('-11971-02-03T04:05:06.125+07:08', (-11971, 2, 2, 20, 57, 6.125)),
                ('1971-02-03T04:05:06.125-07:08', (1971, 2, 3, 11, 13, 6.125)),
                ('1971-02-03T04:05:06.125+07:08', (1971, 2, 2, 20, 57, 6.125)),
                ('-1971-02-03T04:05:06.125-07:08', (-1971, 2, 3, 11, 13, 6.125)),
                ('-1971-02-03T04:05:06.125+07:08', (-1971, 2, 2, 20, 57, 6.125)),

                # Edgepoints (ranges)
                ('2001-01-03T07:08:09Z', (2001, 1, 3, 7, 8, 9)),
                ('2001-12-03T07:08:09Z', (2001, 12, 3, 7, 8, 9)),
                ('2001-02-01T07:08:09Z', (2001, 2, 1, 7, 8, 9)),
                ('2001-02-28T07:08:09Z', (2001, 2, 28, 7, 8, 9)),
                ('2000-02-29T07:08:09Z', (2000, 2, 29, 7, 8, 9)),
                ('1900-02-28T07:08:09Z', (1900, 2, 28, 7, 8, 9)),
                ('2001-02-03T00:08:09Z', (2001, 2, 3, 0, 8, 9)),
                ('2001-02-03T23:08:09Z', (2001, 2, 3, 23, 8, 9)),
                ('2001-02-03T04:00:09Z', (2001, 2, 3, 4, 0, 9)),
                ('2001-02-03T04:59:09Z', (2001, 2, 3, 4, 59, 9)),
                ('2001-02-03T04:05:00Z', (2001, 2, 3, 4, 5, 0)),
                ('2001-02-03T04:05:60.9Z', (2001, 2, 3, 4, 5, 60.9)),
                ('2001-01-31T04:05:06Z', (2001, 1, 31, 4, 5, 6)),
                ('2001-03-31T04:05:06Z', (2001, 3, 31, 4, 5, 6)),
                ('2001-04-30T04:05:06Z', (2001, 4, 30, 4, 5, 6)),
                ('2001-05-31T04:05:06Z', (2001, 5, 31, 4, 5, 6)),
                ('2001-06-30T04:05:06Z', (2001, 6, 30, 4, 5, 6)),
                ('2001-07-31T04:05:06Z', (2001, 7, 31, 4, 5, 6)),
                ('2001-08-31T04:05:06Z', (2001, 8, 31, 4, 5, 6)),
                ('2001-09-30T04:05:06Z', (2001, 9, 30, 4, 5, 6)),
                ('2001-10-31T04:05:06Z', (2001, 10, 31, 4, 5, 6)),
                ('2001-11-30T04:05:06Z', (2001, 11, 30, 4, 5, 6)),
                ('2001-12-31T04:05:06Z', (2001, 12, 31, 4, 5, 6)),

                # Edgepoints (crossing boundaries)
                ('0001-01-01T07:08:23+07:08', (1, 1, 1, 0, 0, 23)),
                ('0001-01-01T07:07:42+07:08', (0, 12, 31, 23, 59, 42)),
                ('-0004-01-01T07:07:42+07:08', (-5, 12, 31, 23, 59, 42)),
                ('2001-03-01T07:07:42+07:08', (2001, 2, 28, 23, 59, 42)),
                ('2000-03-01T07:07:42+07:08', (2000, 2, 29, 23, 59, 42)),
                ('1900-03-01T07:07:42+07:08', (1900, 2, 28, 23, 59, 42)),
            )

        for t in (dateTimeType, timeInstantType, timePeriodType):
            self.allTests(t, baddata, gooddata, parsedata)
            
    # recurringInstant
    def testRecurringInstant(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (1, 2, N, 3, 4, 5),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (1, 2, 3, 4, 5, 'hello'),
                (1, 2, 3.5, 4, 5, 6),
            )
        gooddata = \
            (
                (1L, '1970-01-01T00:00:01Z', (1970, 1, 1, 0, 0, 1.0)),
                (1.5, '1970-01-01T00:00:01.5Z', (1970, 1, 1, 0, 0, 1.5)),
                (1e9, '2001-09-09T01:46:40Z', (2001, 9, 9, 1, 46, 40.0)),
                ((1, 1, 2, 3, 4, 5), '-01-01-02T03:04:05Z',
                    (1, 1, 2, 3, 4, 5)),
                ((-1, 1, 2, 3, 4, 5), '--01-01-02T03:04:05Z',
                    (-1, 1, 2, 3, 4, 5)),
                ((10, 1, 2, 3, 4, 5), '-10-01-02T03:04:05Z',
                    (10, 1, 2, 3, 4, 5)),
                ((-10, 1, 2, 3, 4, 5), '--10-01-02T03:04:05Z',
                    (-10, 1, 2, 3, 4, 5)),
                ((100, 1, 2, 3, 4, 5), '0100-01-02T03:04:05Z',
                    (100, 1, 2, 3, 4, 5)),
                ((-100, 1, 2, 3, 4, 5), '-0100-01-02T03:04:05Z',
                    (-100, 1, 2, 3, 4, 5)),
                ((1970L, 1, 2, 3, 4, 5), '1970-01-02T03:04:05Z',
                    (1970, 1, 2, 3, 4, 5)),
                ((1970L, 1, 2L, 3, 4.0, 5.25), '1970-01-02T03:04:05.25Z',
                    (1970, 1, 2, 3, 4, 5.25)),
                ((11990, 1, 2, 3L, 4, 5.25), '11990-01-02T03:04:05.25Z',
                    (11990, 1, 2, 3, 4, 5.25)),
                ((1e15, 1, 2, 3L, 4, 5.25),
                    '1000000000000000-01-02T03:04:05.25Z',
                    (1e15, 1, 2, 3, 4, 5.25)),
                ((-1e15, 1, 2, 3L, 4, 5.25),
                    '-1000000000000000-01-02T03:04:05.25Z',
                    (-1e15, 1, 2, 3, 4, 5.25)),
                ((N, 1, 2, 3, 4L, 5.25), '---01-02T03:04:05.25Z',
                    (N, 1, 2, 3, 4, 5.25)),
                ((N, N, 2, 3, 4, 5.25, 0, 0, 0), '-----02T03:04:05.25Z',
                    (N, N, 2, 3, 4, 5.25)),
                ((N, N, -2, 3, 4, 5.25, 0, 0, 0), '------02T03:04:05.25Z',
                    (N, N, -2, 3, 4, 5.25)),
                ((N, N, N, 3, 4, 5.25), '------T03:04:05.25Z',
                    (N, N, N, 3, 4, 5.25)),
                ((N, N, N, N, 4, 5.25, 0, 0, 0), '------T-:04:05.25Z',
                    (N, N, N, N, 4, 5.25)),
                ((N, N, N, N, N, 5.25), '------T-:-:05.25Z',
                    (N, N, N, N, N, 5.25)),
                ((N, N, N, N, N, -5.25), '-------T-:-:05.25Z',
                    (N, N, N, N, N, -5.25)),
                ((N, N, N, N, N, N, 0, 0, 0), '------T-:-:-Z',
                    (N, N, N, N, N, N)),
                ((N, N, N, N, N, N, N), '------T-:-:-Z',
                    (N, N, N, N, N, N)),
                ((N, N, N, N, N, N, N, N),
                    '------T-:-:-Z', (N, N, N, N, N, N)),
                ((N, N, N, N, N, N, N, N, N),
                    '------T-:-:-Z', (N, N, N, N, N, N)),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('1970 -01 -01T00:00:01Z', N),
                ('0001-01-01t07:08:23+07:08', N),

                # Invalid ranges
                ('2001-00-03T07:08:23Z', N),
                ('2001-13-03T07:08:23Z', N),
                ('2001-02-00T07:08:23Z', N),
                ('2001-02-29T07:08:23Z', N),
                ('2000-02-30T07:08:23Z', N),
                ('1900-02-29T07:08:23Z', N),
                ('2001-02-03T24:08:23Z', N),
                ('2001-02-03T04:60:23Z', N),
                ('2001-02-03T04:05:61Z', N),
                ('2001-01-32T04:05:06Z', N),
                ('2001-03-32T04:05:06Z', N),
                ('2001-04-31T04:05:06Z', N),
                ('2001-05-32T04:05:06Z', N),
                ('2001-06-31T04:05:06Z', N),
                ('2001-07-32T04:05:06Z', N),
                ('2001-08-32T04:05:06Z', N),
                ('2001-09-31T04:05:06Z', N),
                ('2001-10-32T04:05:06Z', N),
                ('2001-11-31T04:05:06Z', N),
                ('2001-12-32T04:05:06Z', N),

                # Whitespace
                (ws + '1970-01-01T00:00:01Z' + ws, (1970, 1, 1, 0, 0, 1)),

                # No timezones
                ('11971-02-03T04:05:06.125', (11971, 2, 3, 4, 5, 6.125)),
                ('-11971-02-03T04:05:06.125', (-11971, 2, 3, 4, 5, 6.125)),
                ('1971-02-03T04:05:06.125', (1971, 2, 3, 4, 5, 6.125)),
                ('-1971-02-03T04:05:06.125', (-1971, 2, 3, 4, 5, 6.125)),
                ('-71-02-03T04:05:06.125', (71, 2, 3, 4, 5, 6.125)),
                ('--71-02-03T04:05:06.125', (-71, 2, 3, 4, 5, 6.125)),
                ('---02-03T04:05:06.125', (N, 2, 3, 4, 5, 6.125)),
                ('----02-03T04:05:06.125', (N, -2, 3, 4, 5, 6.125)),
                ('-----03T04:05:06.125', (N, N, 3, 4, 5, 6.125)),
                ('------03T04:05:06.125', (N, N, -3, 4, 5, 6.125)),
                ('------T04:05:06.125', (N, N, N, 4, 5, 6.125)),
                ('-------T04:05:06.125', (N, N, N, -4, 5, 6.125)),
                ('------T-:05:06.125', (N, N, N, N, 5, 6.125)),
                ('-------T-:05:06.125', (N, N, N, N, -5, 6.125)),
                ('------T-:-:06.125', (N, N, N, N, N, 6.125)),
                ('-------T-:-:06.125', (N, N, N, N, N, -6.125)),
                ('------T-:-:-', (N, N, N, N, N, N)),
                ('-------T-:-:-', (N, N, N, N, N, N)),

                # Non-zulu
                ('11971-02-03T04:05:06.125-07:08', (11971, 2, 3, 11, 13, 6.125)),
                ('11971-02-03T04:05:06.125+07:08', (11971, 2, 2, 20, 57, 6.125)),
                ('-11971-02-03T04:05:06.125-07:08', (-11971, 2, 3, 11, 13, 6.125)),
                ('-11971-02-03T04:05:06.125+07:08', (-11971, 2, 2, 20, 57, 6.125)),
                ('1971-02-03T04:05:06.125-07:08', (1971, 2, 3, 11, 13, 6.125)),
                ('1971-02-03T04:05:06.125+07:08', (1971, 2, 2, 20, 57, 6.125)),
                ('-1971-02-03T04:05:06.125-07:08', (-1971, 2, 3, 11, 13, 6.125)),
                ('-1971-02-03T04:05:06.125+07:08', (-1971, 2, 2, 20, 57, 6.125)),
                ('-71-02-03T04:05:06.125-07:08', (71, 2, 3, 11, 13, 6.125)),
                ('-71-02-03T04:05:06.125+07:08', (71, 2, 2, 20, 57, 6.125)),
                ('--71-02-03T04:05:06.125-07:08', (-71, 2, 3, 11, 13, 6.125)),
                ('--71-02-03T04:05:06.125+07:08', (-71, 2, 2, 20, 57, 6.125)),
                ('---02-03T04:05:06.125-07:08', (N, 2, 3, 11, 13, 6.125)),
                ('---02-03T04:05:06.125+07:08', (N, 2, 2, 20, 57, 6.125)),
                ('----02-03T04:05:06.125-07:08', (N, -2, 3, 11, 13, 6.125)),
                ('----02-03T04:05:06.125+07:08', (N, -2, 2, 20, 57, 6.125)),
                ('-----03T04:05:06.125-07:08', (N, N, 3, 11, 13, 6.125)),
                ('-----03T04:05:06.125+07:08', (N, N, 2, 20, 57, 6.125)),
                ('------03T04:05:06.125-07:08', (N, N, -3, 11, 13, 6.125)),
                ('------03T04:05:06.125+07:08', (N, N, -4, 20, 57, 6.125)),
                ('------T04:05:06.125-07:08', (N, N, N, 11, 13, 6.125)),
                ('------T04:05:06.125+07:08', (N, N, N, -4, 57, 6.125)),
                ('-------T04:05:06.125-07:08', (N, N, N, 3, 13, 6.125)),
                ('-------T04:05:06.125+07:08', (N, N, N, -12, 57, 6.125)),
                ('------T-:05:06.125-07:08', (N, N, N, N, 433, 6.125)),
                ('------T-:05:06.125+07:08', (N, N, N, N, -423, 6.125)),
                ('-------T-:05:06.125-07:08', (N, N, N, N, 423, 6.125)),
                ('-------T-:05:06.125+07:08', (N, N, N, N, -433, 6.125)),
                ('------T-:-:06.125-07:08', (N, N, N, N, 428, 6.125)),
                ('------T-:-:06.125+07:08', (N, N, N, N, -428, 6.125)),
                ('-------T-:-:06.125-07:08', (N, N, N, N, 427, 53.875)),
                ('-------T-:-:06.125+07:08', (N, N, N, N, -429, 53.875)),
                ('------T-:-:--07:08', (N, N, N, N, 428, 0)),
                ('------T-:-:-+07:08', (N, N, N, N, -428, 0)),
                ('-------T-:-:--07:08', (N, N, N, N, 428, 0)),
                ('-------T-:-:-+07:08', (N, N, N, N, -428, 0)),

                # Edgepoints (ranges)
                ('2001-01-03T07:08:09Z', (2001, 1, 3, 7, 8, 9)),
                ('2001-12-03T07:08:09Z', (2001, 12, 3, 7, 8, 9)),
                ('2001-02-01T07:08:09Z', (2001, 2, 1, 7, 8, 9)),
                ('2001-02-28T07:08:09Z', (2001, 2, 28, 7, 8, 9)),
                ('2000-02-29T07:08:09Z', (2000, 2, 29, 7, 8, 9)),
                ('1900-02-28T07:08:09Z', (1900, 2, 28, 7, 8, 9)),
                ('2001-02-03T00:08:09Z', (2001, 2, 3, 0, 8, 9)),
                ('2001-02-03T23:08:09Z', (2001, 2, 3, 23, 8, 9)),
                ('2001-02-03T04:00:09Z', (2001, 2, 3, 4, 0, 9)),
                ('2001-02-03T04:59:09Z', (2001, 2, 3, 4, 59, 9)),
                ('2001-02-03T04:05:00Z', (2001, 2, 3, 4, 5, 0)),
                ('2001-02-03T04:05:60.9Z', (2001, 2, 3, 4, 5, 60.9)),
                ('2001-01-31T04:05:06Z', (2001, 1, 31, 4, 5, 6)),
                ('2001-03-31T04:05:06Z', (2001, 3, 31, 4, 5, 6)),
                ('2001-04-30T04:05:06Z', (2001, 4, 30, 4, 5, 6)),
                ('2001-05-31T04:05:06Z', (2001, 5, 31, 4, 5, 6)),
                ('2001-06-30T04:05:06Z', (2001, 6, 30, 4, 5, 6)),
                ('2001-07-31T04:05:06Z', (2001, 7, 31, 4, 5, 6)),
                ('2001-08-31T04:05:06Z', (2001, 8, 31, 4, 5, 6)),
                ('2001-09-30T04:05:06Z', (2001, 9, 30, 4, 5, 6)),
                ('2001-10-31T04:05:06Z', (2001, 10, 31, 4, 5, 6)),
                ('2001-11-30T04:05:06Z', (2001, 11, 30, 4, 5, 6)),
                ('2001-12-31T04:05:06Z', (2001, 12, 31, 4, 5, 6)),

                # Edgepoints (crossing boundaries)
                ('0001-01-01T07:08:23+07:08', (1, 1, 1, 0, 0, 23)),
                ('0001-01-01T07:07:42+07:08', (0, 12, 31, 23, 59, 42)),
                ('-0004-01-01T07:07:42+07:08', (-5, 12, 31, 23, 59, 42)),
                ('2001-03-01T07:07:42+07:08', (2001, 2, 28, 23, 59, 42)),
                ('2000-03-01T07:07:42+07:08', (2000, 2, 29, 23, 59, 42)),
                ('1900-03-01T07:07:42+07:08', (1900, 2, 28, 23, 59, 42)),
                ('---03-01T07:07:42+07:08', (N, 2, 28, 23, 59, 42)),
            )

        for t in (recurringInstantType,):
            self.allTests(t, baddata, gooddata, parsedata)

    def testTime(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (1, 2, 3, 4, 5),
                (1, 2, 3, 4, 5, 6, 7, 8),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (1, 2, 'hello'),
                (1, 2.5, 3),
                (25, 0, 0),
                (1, 60, 0),
                (1, 0, 61),
            )
        gooddata = \
            (
                (1L, '00:00:01Z', (0, 0, 1.0)),
                (1.5, '00:00:01.5Z', (0, 0, 1.5)),
                (3661.5, '01:01:01.5Z', (1, 1, 1.5)),
                (86399.75, '23:59:59.75Z', (23, 59, 59.75)),
                ((1,), '01:00:00Z', (1, 0, 0)),
                ((1, 2), '01:02:00Z', (1, 2, 0)),
                ((10L, 20.0, 30), '10:20:30Z', (10, 20, 30.0)),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('00 00:01Z', N),
                ('07:O8:23Z', N),

                # Invalid ranges
                ('24:08:23Z', N),
                ('04:60:23Z', N),
                ('04:05:61Z', N),

                # Whitespace
                (ws + '00:00:01Z' + ws, (0, 0, 1)),

                # No timezones
                ('04:05:06.125', (4, 5, 6.125)),

                # Non-zulu
                ('04:05:06.125-07:08', (11, 13, 6.125)),
                ('04:05:06.125+07:08', (-4, 57, 6.125)),

                # Edgepoints (ranges)
                ('00:08:09Z', (0, 8, 9)),
                ('23:08:09Z', (23, 8, 9)),
                ('04:00:09Z', (4, 0, 9)),
                ('04:59:09Z', (4, 59, 9)),
                ('04:05:00Z', (4, 5, 0)),
                ('04:05:60.9Z', (4, 5, 60.9)),

                # Edgepoints (crossing boundaries)
                ('07:08:23+07:08', (0, 0, 23)),
                ('07:07:42+07:08', (-1, 59, 42)),
            )

        for t in (timeType,):
            self.allTests(t, baddata, gooddata, parsedata)
        
    def testDate(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (1, 2, 3, 4, 5),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (1, 2, 3, 4, 5, 'hello'),
                (1, 2.5, 3, 4, 5, 6),
                (1, 2, 3.5),
                (1, 0, 3),
                (1, 13, 3),
                (1, 1, 0),
                (1, 1, 32),
                (1, 2, 29),
                (0, 2, 30),
                (100, 2, 29),
                (1, 3, 32),
                (1, 4, 31),
                (1, 5, 32),
                (1, 6, 31),
                (1, 7, 32),
                (1, 8, 32),
                (1, 9, 31),
                (1, 10, 32),
                (1, 11, 31),
                (1, 12, 32),
            )
        gooddata = \
            (
                (1L, '1970-01-01Z', (1970, 1, 1)),
                (1.5, '1970-01-01Z', (1970, 1, 1)),
                ((2,), '0002-01-01Z', (2, 1, 1)),
                ((2, 3), '0002-03-01Z', (2, 3, 1)),
                ((-2, 3, 4), '-0002-03-04Z', (-2, 3, 4)),
                ((2, 3, 4), '0002-03-04Z', (2, 3, 4)),
                ((10, 2, 3), '0010-02-03Z', (10, 2, 3)),
                ((100, 2, 3), '0100-02-03Z', (100, 2, 3)),
                ((1970, 2, 3), '1970-02-03Z', (1970, 2, 3)),
                ((-1970, 2, 3), '-1970-02-03Z', (-1970, 2, 3)),
                ((1970L, 2.0, 3.0), '1970-02-03Z', (1970, 2, 3)),
                ((11990, 1L, 2), '11990-01-02Z', (11990, 1, 2)),
                ((1e15, 1, 2), '1000000000000000-01-02Z', (1e15, 1, 2)),
                ((-1e15, 1, 2), '-1000000000000000-01-02Z', (-1e15, 1, 2)),
                ((1000000000000000L, 1, 2), '1000000000000000-01-02Z',
                    (1e15, 1, 2)),
                ((-1000000000000000L, 1, 2), '-1000000000000000-01-02Z',
                    (-1e15, 1, 2)),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('1970 -01 -01Z', N),
                ('0001-02-03z', N),

                # Invalid ranges
                ('2001-00-03Z', N),
                ('2001-13-03Z', N),
                ('2001-02-00Z', N),
                ('2001-02-29Z', N),
                ('2000-02-30Z', N),
                ('1900-02-29Z', N),
                ('2001-01-32Z', N),
                ('2001-03-32Z', N),
                ('2001-04-31Z', N),
                ('2001-05-32Z', N),
                ('2001-06-31Z', N),
                ('2001-07-32Z', N),
                ('2001-08-32Z', N),
                ('2001-09-31Z', N),
                ('2001-10-32Z', N),
                ('2001-11-31Z', N),
                ('2001-12-32Z', N),

                # Whitespace
                (ws + '1970-01-01Z' + ws, (1970, 1, 1)),

                # No timezones
                ('11971-02-03', (11971, 2, 3)),
                ('1971-02-03', (1971, 2, 3)),
                ('-1971-02-03', (-1971, 2, 3)),

                # Non-zulu
                ('11971-02-03-07:08', (11971, 2, 3)),
                ('11971-02-03+07:08', (11971, 2, 2)),
                ('-11971-02-03-07:08', (-11971, 2, 3)),
                ('-11971-02-03+07:08', (-11971, 2, 2)),
                ('1971-02-03-07:08', (1971, 2, 3)),
                ('1971-02-03+07:08', (1971, 2, 2)),
                ('-1971-02-03-07:08', (-1971, 2, 3)),
                ('-1971-02-03+07:08', (-1971, 2, 2)),

                # Edgepoints (ranges)
                ('2001-01-03Z', (2001, 1, 3)),
                ('2001-12-03Z', (2001, 12, 3)),
                ('2001-02-01Z', (2001, 2, 1)),
                ('2001-02-28Z', (2001, 2, 28)),
                ('2000-02-29Z', (2000, 2, 29)),
                ('1900-02-28Z', (1900, 2, 28)),
                ('2001-01-31Z', (2001, 1, 31)),
                ('2001-03-31Z', (2001, 3, 31)),
                ('2001-04-30Z', (2001, 4, 30)),
                ('2001-05-31Z', (2001, 5, 31)),
                ('2001-06-30Z', (2001, 6, 30)),
                ('2001-07-31Z', (2001, 7, 31)),
                ('2001-08-31Z', (2001, 8, 31)),
                ('2001-09-30Z', (2001, 9, 30)),
                ('2001-10-31Z', (2001, 10, 31)),
                ('2001-11-30Z', (2001, 11, 30)),
                ('2001-12-31Z', (2001, 12, 31)),

                # Edgepoints (crossing boundaries)
                ('0001-01-01+07:08', (0, 12, 31)),
                ('-0004-01-01+07:08', (-5, 12, 31)),
                ('2001-03-01+07:08', (2001, 2, 28)),
                ('2000-03-01+07:08', (2000, 2, 29)),
                ('1900-03-01+07:08', (1900, 2, 28)),
            )

        for t in (dateType,):
            self.allTests(t, baddata, gooddata, parsedata)

    def testGYearMonth(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (1, 2, 3),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (1, 2, 3.5),
                (1, 'hello'),
                (1, 2.5),
                (1, 0),
                (1, 13),
            )
        gooddata = \
            (
                (1L, '1970-01Z', (1970, 1)),
                (1.5, '1970-01Z', (1970, 1)),
                ((2,), '0002-01Z', (2, 1)),
                ((2, 3), '0002-03Z', (2, 3)),
                ((-2, 3), '-0002-03Z', (-2, 3)),
                ((10, 2), '0010-02Z', (10, 2)),
                ((100, 2), '0100-02Z', (100, 2)),
                ((1970, 2), '1970-02Z', (1970, 2)),
                ((-1970, 2), '-1970-02Z', (-1970, 2)),
                ((1970L, 2.0), '1970-02Z', (1970, 2)),
                ((11990, 1L), '11990-01Z', (11990, 1)),
                ((1e15, 1), '1000000000000000-01Z', (1e15, 1)),
                ((-1e15, 1), '-1000000000000000-01Z', (-1e15, 1)),
                ((1000000000000000L, 1), '1000000000000000-01Z', (1e15, 1)),
                ((-1000000000000000L, 1), '-1000000000000000-01Z', (-1e15, 1)),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('1970 -01Z', N),
                ('0001-02z', N),

                # Invalid ranges
                ('2001-00Z', N),
                ('2001-13Z', N),

                # Whitespace
                (ws + '1970-01Z' + ws, (1970, 1)),

                # No timezones
                ('11971-02', (11971, 2)),
                ('1971-02', (1971, 2)),
                ('-1971-02', (-1971, 2)),

                # Non-zulu
                ('11971-02-07:08', (11971, 2)),
                ('11971-02+07:08', (11971, 1)),
                ('-11971-02-07:08', (-11971, 2)),
                ('-11971-02+07:08', (-11971, 1)),
                ('1971-02-07:08', (1971, 2)),
                ('1971-02+07:08', (1971, 1)),
                ('-1971-02-07:08', (-1971, 2)),
                ('-1971-02+07:08', (-1971, 1)),

                # Edgepoints (ranges)
                ('2001-01Z', (2001, 1)),
                ('2001-12Z', (2001, 12)),

                # Edgepoints (crossing boundaries)
                ('0001-01+07:08', (0, 12)),
                ('-0004-01+07:08', (-5, 12)),
                ('2001-03+07:08', (2001, 2)),
                ('2000-03+07:08', (2000, 2)),
                ('1900-03+07:08', (1900, 2)),
            )

        for t in (gYearMonthType,):
            self.allTests(t, baddata, gooddata, parsedata)

    def testGYearAndYear(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (1, 2),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (2.5,),
            )
        gooddata = \
            (
                (1L, '0001Z', 1),
                (10, '0010Z', 10),
                (100, '0100Z', 100),
                (1970, '1970Z', 1970),
                (-1970, '-1970Z', -1970),
                (1970L, '1970Z', 1970),
                (11990.0, '11990Z', 11990),
                (1e15, '1000000000000000Z', 1e15),
                (-1e15, '-1000000000000000Z', -1e15),
                (1000000000000000L, '1000000000000000Z', 1e15),
                (-1000000000000000L, '-1000000000000000Z', -1e15),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('197OZ', N),
                ('0001z', N),

                # Whitespace
                (ws + '1970Z' + ws, 1970),

                # No timezones
                ('11971', 11971),
                ('1971', 1971),
                ('-1971', -1971),

                # Non-zulu
                ('11971-07:08', 11971),
                ('11971+07:08', 11970),
                ('-11971-07:08', -11971),
                ('-11971+07:08', -11972),
                ('1971-07:08', 1971),
                ('1971+07:08', 1970),
                ('-1971-07:08', -1971),
                ('-1971+07:08', -1972),

                # Edgepoints (crossing boundaries)
                ('0001+07:08', 0),
                ('-0004+07:08', -5),
            )

        for t in (gYearType, yearType):
            self.allTests(t, baddata, gooddata, parsedata)

    def testCentury(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (1, 2),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (2.5,),
            )
        gooddata = \
            (
                (1L, '01Z', 1),
                (10, '10Z', 10),
                (100, '100Z', 100),
                (19, '19Z', 19),
                (-19, '-19Z', -19),
                (19L, '19Z', 19),
                (119.0, '119Z', 119),
                (1e15, '1000000000000000Z', 1e15),
                (-1e15, '-1000000000000000Z', -1e15),
                (1000000000000000L, '1000000000000000Z', 1e15),
                (-1000000000000000L, '-1000000000000000Z', -1e15),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('197OZ', N),
                ('0001z', N),

                # Whitespace
                (ws + '1970Z' + ws, 1970),

                # No timezones
                ('11971', 11971),
                ('1971', 1971),
                ('-1971', -1971),

                # Non-zulu
                ('11971-07:08', 11971),
                ('11971+07:08', 11970),
                ('-11971-07:08', -11971),
                ('-11971+07:08', -11972),
                ('1971-07:08', 1971),
                ('1971+07:08', 1970),
                ('-1971-07:08', -1971),
                ('-1971+07:08', -1972),

                # Edgepoints (crossing boundaries)
                ('0001+07:08', 0),
                ('-0004+07:08', -5),
            )

        for t in (centuryType,):
            self.allTests(t, baddata, gooddata, parsedata)

    def testGMonthDayAndRecurringDate(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (3, 4, 5),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (4, 5, 'hello'),
                (2.5, 3),
                (0, 3),
                (13, 3),
                (1, 0),
                (1, 32),
                (2, 29),
                (3, 32),
                (4, 31),
                (5, 32),
                (6, 31),
                (7, 32),
                (8, 32),
                (9, 31),
                (10, 32),
                (11, 31),
                (12, 32),
            )
        gooddata = \
            (
                (1L, '--01-01Z', (1, 1)),
                (1.5, '--01-01Z', (1, 1)),
                ((2,), '--02-01Z', (2, 1)),
                ((2, 3), '--02-03Z', (2, 3)),
                ((10, 2), '--10-02Z', (10, 2)),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('--01 -01Z', N),
                ('--02-03z', N),

                # Invalid ranges
                ('--00-03Z', N),
                ('--13-03Z', N),
                ('--01-32Z', N),
                ('--02-00Z', N),
                ('--02-29Z', N),
                ('--03-32Z', N),
                ('--04-31Z', N),
                ('--05-32Z', N),
                ('--06-31Z', N),
                ('--07-32Z', N),
                ('--08-32Z', N),
                ('--09-31Z', N),
                ('--10-32Z', N),
                ('--11-31Z', N),
                ('--12-32Z', N),

                # Whitespace
                (ws + '--01-01Z' + ws, (1, 1)),

                # No timezones
                ('--02-03', (2, 3)),

                # Non-zulu
                ('--02-03-07:08', (2, 3)),
                ('--02-03+07:08', (2, 2)),

                # Edgepoints (ranges)
                ('--01-03Z', (1, 3)),
                ('--12-03Z', (12, 3)),
                ('--01-31Z', (1, 31)),
                ('--02-01Z', (2, 1)),
                ('--02-28Z', (2, 28)),
                ('--03-31Z', (3, 31)),
                ('--04-30Z', (4, 30)),
                ('--05-31Z', (5, 31)),
                ('--06-30Z', (6, 30)),
                ('--07-31Z', (7, 31)),
                ('--08-31Z', (8, 31)),
                ('--09-30Z', (9, 30)),
                ('--10-31Z', (10, 31)),
                ('--11-30Z', (11, 30)),
                ('--12-31Z', (12, 31)),

                # Edgepoints (crossing boundaries)
                ('--01-01+07:08', (12, 31)),
                ('--03-01+07:08', (2, 28)),
            )

        for t in (gMonthDayType, recurringDateType):
            self.allTests(t, baddata, gooddata, parsedata)
            
    def testGMonthAndMonth(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (3, 4,),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (2.5,),
                (0,),
                (13,),
            )
        gooddata = \
            (
                (1L, '--01--Z', 1),
                ((2,), '--02--Z', 2),
                ((10,), '--10--Z', 10),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('--01 --Z', N),
                ('--03--z', N),

                # Invalid ranges
                ('--00--Z', N),
                ('--13--Z', N),

                # Whitespace
                (ws + '--01--Z' + ws, 1),

                # No timezones
                ('--03--', 3),

                # Non-zulu
                ('--03---07:08', 3),
                ('--03--+07:08', 2),

                # Edgepoints (ranges)
                ('--01--Z', 1),
                ('--12--Z', 12),

                # Edgepoints (crossing boundaries)
                ('--01--+07:08', 12),
                ('--12---07:08', 12),
            )

        for t in (gMonthType, monthType):
            self.allTests(t, baddata, gooddata, parsedata)
            
    def testGDayAndRecurringDay(self):
        baddata = \
            (
                'hello',
                ('hello',),
                (3, 4,),
                (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
                (2.5,),
                (0,),
                (32,),
            )
        gooddata = \
            (
                (1L, '---01Z', 1),
                ((2,), '---02Z', 2),
                ((10,), '---10Z', 10),
            )
        parsedata = \
            (
                # Some strings that won't match the r.e.
                ('hello', N),
                ('---01 Z', N),
                ('---03z', N),

                # Invalid ranges
                ('---00Z', N),
                ('---32Z', N),

                # Whitespace
                (ws + '---01Z' + ws, 1),

                # No timezones
                ('---03', 3),

                # Non-zulu
                ('---03-07:08', 3),
                ('---03+07:08', 2),

                # Edgepoints (ranges)
                ('---01Z', 1),
                ('---31Z', 31),

                # Edgepoints (crossing boundaries)
                ('---01+07:08', 31),
                ('---31-07:08', 31),
            )

        for t in (gDayType, recurringDayType):
            self.allTests(t, baddata, gooddata, parsedata)
            
    def testInteger(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {})
        t = integerType
        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (10, 23L, 1111111111111111111111111111111111111111111111111111L):
            x = integerType(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('10 000', N),
            ('1', 1),
            ('123456789012345678901234567890', 123456789012345678901234567890L),
            (ws + '12' + ws, 12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4],
                    i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testNonPositiveInteger(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, 1, 23)
        for t in (nonPositiveIntegerType, non_Positive_IntegerType):
            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a t with a bad value (%s)" % \
                            (t.__name__, repr(i))
                except AssertionError:
                    raise
                except ValueError:
                    pass

            # Now some things that should

            for i in (0, -23L, -1111111111111111111111111111111111111111111111111L):
                x = t(i)
                d = x._marshalData()

                if d != str(i):
                    raise AssertionError, "expected %d, got %s" % (i, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != i:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))

            # Now test parsing, both valid and invalid

            test = (('hello', N), ('3.14', N), ('-10 000', N), ('1', N),
                ('0', 0),
                ('-1', -1),
                ('-123456789012345678901234567890', -123456789012345678901234567890L),
                (ws + '-12' + ws, -12))

            for i in test:
                try:
                    if t == nonPositiveIntegerType:
                        n = t.__name__[:-4]
                    else:
                        n = 'non-positive-integer'

                    z = parseSOAPRPC(self.build_xml(t._validURIs[0], n, i[0]))

                    if z != i[1]:
                        raise AssertionError, "%s: expected %s, got %s" % \
                            (i[0], i[1], repr(z))
                except AssertionError:
                    raise
                except:
                    if i[1] != N:
                        raise AssertionError, \
                            "parsing %s as %s threw exception %s:%s" % \
                            (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testNegativeInteger(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, 0, 23)
        for t in (negativeIntegerType, negative_IntegerType):
            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a %s with a bad value (%s)" % \
                            (t.__name__, repr(i))
                except AssertionError:
                    raise
                except ValueError:
                    pass

            # Now some things that should

            for i in (-1, -23L, -111111111111111111111111111111111111111111111111L):
                x = t(i)
                d = x._marshalData()

                if d != str(i):
                    raise AssertionError, "expected %d, got %s" % (i, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != i:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))

            # Now test parsing, both valid and invalid

            test = (('hello', N), ('3.14', N), ('-10 000', N), ('1', N),
                ('0', N),
                ('-1', -1),
                ('-123456789012345678901234567890', -123456789012345678901234567890L),
                (ws + '-12' + ws, -12))

            for i in test:
                try:
                    if t == negativeIntegerType:
                        n = t.__name__[:-4]
                    else:
                        n = 'negative-integer'

                    z = parseSOAPRPC(self.build_xml(t._validURIs[0], n, i[0]))

                    if z != i[1]:
                        raise AssertionError, "expected %s, got %s" % (i[1], repr(z))
                except AssertionError:
                    raise
                except:
                    if i[1] != N:
                        raise AssertionError, \
                            "parsing %s as %s threw exception %s:%s" % \
                            (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testLong(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {},
            -9223372036854775809L, 9223372036854775808L)
        t = longType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (-1, -23L, -9223372036854775808L, 9223372036854775807L):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N),
            ('-9223372036854775809', N), ('9223372036854775808', N),
            ('-1', -1), ('0', 0), ('1', 1),
            ('-9223372036854775808', -9223372036854775808L),
            ('9223372036854775807', 9223372036854775807L),
            (ws + '-12' + ws, -12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testInt(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -2147483649L, 2147483648L)
        t = intType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (-1, -23L, -2147483648L, 2147483647):
            x = intType(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N),
            ('-2147483649', N), ('2147483648', N),
            ('-1', -1), ('0', 0), ('1', 1),
            ('-2147483648', -2147483648L),
            ('2147483647', 2147483647),
            (ws + '-12' + ws, -12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])                

    def testShort(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -32769, 32768)
        t = shortType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (-1, -23L, -32768, 32767):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N),
            ('-32769', N), ('32768', N),
            ('-1', -1), ('0', 0), ('1', 1),
            ('-32768', -32768),
            ('32767', 32767),
            (ws + '-12' + ws, -12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testByte(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -129, 128)
        t = byteType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (-1, -23L, -128, 127):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N),
            ('-129', N), ('128', N),
            ('-1', -1), ('0', 0), ('1', 1),
            ('-128', -128),
            ('127', 127),
            (ws + '-12' + ws, -12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testNonNegativeInteger(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -42, -1)
        for t in (nonNegativeIntegerType, non_Negative_IntegerType):
            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a %s with a bad value (%s)" % \
                            (t.__name__, repr(i))
                except AssertionError:
                    raise
                except ValueError:
                    pass

            # Now some things that should

            for i in (0, 1, 23L, 111111111111111111111111111111111111111111111111L):
                x = t(i)
                d = x._marshalData()

                if d != str(i):
                    raise AssertionError, "expected %d, got %s" % (i, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != i:
                    raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

            # Now test parsing, both valid and invalid

            test = (('hello', N), ('3.14', N), ('-10 000', N), ('-1', N),
                ('0', 0),
                ('1', 1),
                ('123456789012345678901234567890', 123456789012345678901234567890L),
                (ws + '12' + ws, 12))

            for i in test:
                try:
                    if t == nonNegativeIntegerType:
                        n = t.__name__[:-4]
                    else:
                        n = 'non-negative-integer'

                    z = parseSOAPRPC(self.build_xml(t._validURIs[0], n, i[0]))

                    if z != i[1]:
                        raise AssertionError, "%s: expected %s, got %s" % \
                            (i[0], i[1], repr(z))
                except AssertionError:
                    raise
                except:
                    if i[1] != N:
                        raise AssertionError, \
                            "parsing %s as %s threw exception %s:%s" % \
                            (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testUnsignedLong(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -42, -1, 18446744073709551616L)
        t = unsignedLongType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (0, 23L, 18446744073709551615L):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N), ('-1', N),
            ('18446744073709551616', N),
            ('0', 0), ('1', 1),
            ('18446744073709551615', 18446744073709551615L),
            (ws + '12' + ws, 12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testUnsignedInt(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -42, -1, 4294967296L)
        t = unsignedIntType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (0, 23L, 4294967295L):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N), ('-1', N),
            ('4294967296', N),
            ('0', 0), ('1', 1),
            ('4294967295', 4294967295L),
            (ws + '12' + ws, 12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])
                
    def testUnsignedShort(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -42, -1, 65536)
        t = unsignedShortType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (0, 23L, 65535):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N), ('-1', N),
            ('65536', N),
            ('0', 0), ('1', 1),
            ('65535', 65535),
            (ws + '12' + ws, 12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testUnsignedByte(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -42, -1, 256)
        t = unsignedByteType

        for i in test:
            try:
                t(i)
                raise AssertionError, \
                    "instantiated a %s with a bad value (%s)" % \
                        (t.__name__, repr(i))
            except AssertionError:
                raise
            except ValueError:
                pass

        # Now some things that should

        for i in (0, 23L, 255):
            x = t(i)
            d = x._marshalData()

            if d != str(i):
                raise AssertionError, "expected %d, got %s" % (i, d)

            y = buildSOAP(x)
            z = parseSOAPRPC(y)

            if z != i:
                raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

        # Now test parsing, both valid and invalid

        test = (('hello', N), ('3.14', N), ('-10 000', N), ('-1', N),
            ('256', N),
            ('0', 0), ('1', 1),
            ('255', 255),
            (ws + '12' + ws, 12))

        for i in test:
            try:
                z = parseSOAPRPC(self.build_xml(t._validURIs[0], t.__name__[:-4], i[0]))

                if z != i[1]:
                    raise AssertionError, "%s: expected %s, got %s" % \
                        (i[0], i[1], repr(z))
            except AssertionError:
                raise
            except:
                if i[1] != N:
                    raise AssertionError, \
                        "parsing %s as %s threw exception %s:%s" % \
                        (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testPositiveInteger(self):
        # First some things that shouldn't be valid
        test = ('hello', 3.14, (), [], {}, -42, -1, 0)
        for t in (positiveIntegerType, positive_IntegerType):
            for i in test:
                try:
                    t(i)
                    raise AssertionError, \
                        "instantiated a t with a bad value (%s)" % \
                            (t.__name__, repr(i))
                except AssertionError:
                    raise
                except ValueError:
                    pass

            # Now some things that should

            for i in (1, 23L, 1111111111111111111111111111111111111111111111111111L):
                x = t(i)
                d = x._marshalData()

                if d != str(i):
                    raise AssertionError, "expected %d, got %s" % (i, d)

                y = buildSOAP(x)
                z = parseSOAPRPC(y)

                if z != i:
                    raise AssertionError, "expected %s, got %s" % (repr(i), repr(z))

            # Now test parsing, both valid and invalid

            test = (('hello', N), ('3.14', N), ('-10 000', N), ('-1', N),
                ('0', N), ('1', 1),
                ('123456789012345678901234567890', 123456789012345678901234567890L),
                (ws + '12' + ws, 12))

            for i in test:
                try:
                    if t == positiveIntegerType:
                        n = t.__name__[:-4]
                    else:
                        n = 'positive-integer'

                    z = parseSOAPRPC(self.build_xml(t._validURIs[0], n, i[0]))

                    if z != i[1]:
                        raise AssertionError, "%s: expected %s, got %s" % \
                            (i[0], i[1], repr(z))
                except AssertionError:
                    raise
                except:
                    if i[1] != N:
                        raise AssertionError, \
                            "parsing %s as %s threw exception %s:%s" % \
                            (i[0], t.__name__, sys.exc_info()[0], sys.exc_info()[1])

    def testUntyped(self):
        # Make sure untypedType really isn't typed
        a = stringType('hello', name = 'a')
        b = untypedType('earth', name = 'b')

        x = buildSOAP((a, b))
        #print "x=",x

        self.failUnless(x.find('<a xsi:type="xsd:string" SOAP-ENC:root="1">hello</a>') != -1)
        self.failUnless(x.find('<b SOAP-ENC:root="1">earth</b>') != -1)
        
    # Now some Array tests
    def testArray(self):
        env = '''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsd2="http://www.w3.org/2000/10/XMLSchema" xmlns:xsd3="http://www.w3.org/2001/XMLSchema" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/">
%s
</SOAP-ENV:Envelope>'''

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[4]" SOAP-ENC:offset="[2]" xsi:type="SOAP-ENC:Array">
    <_2 SOAP-ENC:arrayType="xsd:int[2]" xsi:type="SOAP-ENC:Array">
        <item>1</item>
        <item>2</item>
    </_2>
    <_3 SOAP-ENC:arrayType="xsd:int[2]" xsi:type="SOAP-ENC:Array">
        <item>3</item>
        <item>4</item>
    </_3>
</_1>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [None, None, [1, 2], [3, 4]])

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[3,4,2]" SOAP-ENC:offset="[17]" xsi:type="SOAP-ENC:Array">
    <item>1</item>
    <item>2</item>
    <item>3</item>
    <item>4</item>
    <item>5</item>
    <item>6</item>
    <item>7</item>
</_1>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [
            [[None, None], [None, None], [None, None], [None, None]],
            [[None, None], [None, None], [None, None], [None, None]],
            [[None, 1], [2, 3], [4, 5], [6, 7]]
        ])

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[3,4,2]" xsi:type="SOAP-ENC:Array">
    <item SOAP-ENC:position="[17]">-17</item>
    <item SOAP-ENC:position="[13]">13</item>
    <item SOAP-ENC:position="[22]">-22</item>
    <item SOAP-ENC:position="[1]">1</item>
    <item SOAP-ENC:position="[17]">17</item>
    <item SOAP-ENC:position="[23]">23</item>
    <item SOAP-ENC:position="[6]">6</item>
</_1>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [
            [[None, 1L], [None, None], [None, None], [6L, None]],
            [[None, None], [None, None], [None, 13L], [None, None]],
            [[None, 17L], [None, None], [None, None], [-22L, 23L]]
        ])

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[4]" SOAP-ENC:offset="[3]" xsi:type="SOAP-ENC:Array">
    <item SOAP-ENC:position="[2]">2</item>
    <item SOAP-ENC:position="[0]">0</item>
    <item SOAP-ENC:position="[1]">1</item>
    <item SOAP-ENC:position="[3]">3</item>
</_1>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [0, 1, 2, 3])

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,3,4]" SOAP-ENC:offset="[23]" xsi:type="SOAP-ENC:Array">
</_1>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [
            [
                [None, None, None, None],
                [None, None, None, None],
                [None, None, None, None],
            ],
            [
                [None, None, None, None],
                [None, None, None, None],
                [None, None, None, None],
            ]
        ])

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[4]" SOAP-ENC:offset="[3]" xsi:type="SOAP-ENC:Array">
    <item>2</item>
    <item>3</item>
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "full array parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,0,4]" xsi:type="SOAP-ENC:Array">
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "array with bad dimension (0) parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,3,-4]" xsi:type="SOAP-ENC:Array">
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "array with bad dimension (negative) parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,3,4.4]" xsi:type="SOAP-ENC:Array">
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "array with bad dimension (non-integral) parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,hello,4]" xsi:type="SOAP-ENC:Array">
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "array with bad dimension (non-numeric) parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,3,4]" SOAP-ENC:offset="[-4]" xsi:type="SOAP-ENC:Array">
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "array with too large offset parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,3,4]" SOAP-ENC:offset="[24]" xsi:type="SOAP-ENC:Array">
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "array with too large offset parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
<_1 SOAP-ENC:arrayType="xsd:int[2,3,4]" xsi:type="SOAP-ENC:Array">
    <item SOAP-ENC:position="0">2</item>
    <item>3</item>
</_1>
</SOAP-ENV:Body>'''

        try:
            x = parseSOAPRPC(xml)
            raise AssertionError, "full array parsed"
        except AssertionError:
            raise
        except:
            pass

        xml = env % '''<SOAP-ENV:Body>
    <myFavoriteNumbers type="SOAP-ENC:Array" SOAP-ENC:arrayType="xsd:int[2]">
        <number>3</number> 
        <number>4</number> 
    </myFavoriteNumbers>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [3, 4])

        xml = env % '''<SOAP-ENV:Body>
<SOAP-ENC:Array SOAP-ENC:arrayType="xsd:ur-type[4]">
   <thing xsi:type="xsd:int">12345</thing>
   <thing xsi:type="xsd:decimal">6.789</thing>
   <thing xsi:type="xsd:string">Of Mans First Disobedience, and the Fruit
Of that Forbidden Tree, whose mortal tast
Brought Death into the World, and all our woe,</thing>
   <thing xsi:type="xsd2:uriReference">
      http://www.dartmouth.edu/~milton/reading_room/
   </thing>
</SOAP-ENC:Array>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [12345, 6.789, '''Of Mans First Disobedience, and the Fruit
Of that Forbidden Tree, whose mortal tast
Brought Death into the World, and all our woe,''',
      'http://www.dartmouth.edu/~milton/reading_room/'])

        xml = env % '''<SOAP-ENV:Body>
<SOAP-ENC:Array SOAP-ENC:arrayType="xyz:Order[2]">
   <Order>
       <Product>Apple</Product>
       <Price>1.56</Price>
   </Order>
   <Order>
       <Product>Peach</Product>
       <Price>1.48</Price>
   </Order>
</SOAP-ENC:Array>
</SOAP-ENV:Body>'''

        #x = parseSOAPRPC(xml)

        #print "x=",x

        xml = env % '''<SOAP-ENV:Body>
<SOAP-ENC:Array SOAP-ENC:arrayType="xsd:string[3]">
   <item href="#array-1"/>
   <item href="#array-2"/>
   <item href="#array-2"/>
</SOAP-ENC:Array>
<SOAP-ENC:Array id="array-1" SOAP-ENC:arrayType="xsd:string[3]">
   <item>r1c1</item>
   <item>r1c2</item>
   <item>r1c3</item>
</SOAP-ENC:Array>
<SOAP-ENC:Array id="array-2" SOAP-ENC:arrayType="xsd:string[2]">
   <item>r2c1</item>
   <item>r2c2</item>
</SOAP-ENC:Array>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [['r1c1', 'r1c2', 'r1c3'],
                                 ['r2c1', 'r2c2'], ['r2c1', 'r2c2']])

        xml = env % '''<SOAP-ENV:Body>
<SOAP-ENC:Array SOAP-ENC:arrayType="xsd:string[2,3]">
   <item>r1c1</item> 
   <item>r1c2</item> 
   <item>r1c3</item> 
   <item>r2c1</item> 
   <item>r2c2</item> 
   <item>r2c3</item> 
</SOAP-ENC:Array>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [['r1c1', 'r1c2', 'r1c3'], ['r2c1', 'r2c2', 'r2c3']])

        xml = env % '''<SOAP-ENV:Body>
<SOAP-ENC:Array SOAP-ENC:arrayType="xsd:string[5]" SOAP-ENC:offset="[2]">
   <item>The third element</item>
   <item>The fourth element</item>
</SOAP-ENC:Array>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

        self.assertEquals( x ,  [None, None, 'The third element', 'The fourth element', None])

        xml = env % '''<SOAP-ENV:Body>
<SOAP-ENC:Array SOAP-ENC:arrayType="xsd:string[,][4]">
   <SOAP-ENC:Array href="#array-1" SOAP-ENC:position="[2]"/>
</SOAP-ENC:Array>
<SOAP-ENC:Array id="array-1" SOAP-ENC:arrayType="xsd:string[10,10]">
   <item SOAP-ENC:position="[2,2]">Third row, third col</item>
   <item SOAP-ENC:position="[7,2]">Eighth row, third col</item>
</SOAP-ENC:Array>
</SOAP-ENV:Body>'''

        x = parseSOAPRPC(xml)

    # Example using key data
    def testKeyData(self):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:dsig="http://www.w3.org/2000/09/xmldsig#" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/1999/XMLSchema" xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
<soap:Body>
    <xkms:RegisterResult xmlns:xkms="http://www.xkms.org/schema/xkms-2001-01-20">
        <xkms:Result>Success</xkms:Result>
        <xkms:Answer soapenc:arrayType="KeyBinding[1]">
            <xkms:KeyBinding>
                <xkms:Status>Valid</xkms:Status>
                <xkms:KeyID>mailto:actzerotestkeyname</xkms:KeyID>
                <dsig:KeyInfo>
                    <dsig:X509Data>
                        <dsig:X509Certificate>MIIDPjCCAqegAwIBAgIEOroMvDANBgkqhkiG9w0BAQUFADAxMQswCQYDVQQGEwJVI3nlMkH84ZdPKIyz60sNcVEwJ8kF+B6ZVNimCF+r7BWgLi/Dolce5CpbfMMyexZ+UQEMADrc7331eYS891KXSDQx</dsig:X509Certificate>
                    </dsig:X509Data>
                    <dsig:KeyName>mailto:actzerotestkeyname</dsig:KeyName>
                    <dsig:KeyValue>
                        <dsig:RSAKeyValue>
                            <dsig:Modulus>wgmV2FY6MBKvtaMmCvCoNi/0hycZkiPKC2PXjRLJKFJ5wjNfF+vWsQQUXxOKUQnu
HjJqRkx90jJvnEzW3j9FlZFQcZTfJbE0v6BXhhSre2kZvkgcOERmDMeMs//oEA4u
epnedUwrkPzedWU9AL7c/oN7rk65UuPWf7V8c/4E9bc=</dsig:Modulus>
                            <dsig:Exponent>AQAB</dsig:Exponent>
                        </dsig:RSAKeyValue>
                    </dsig:KeyValue>
                </dsig:KeyInfo>
            </xkms:KeyBinding>
        </xkms:Answer>
        <xkms:Private>9GKuRC3ISwE9aEatzDKW0WIp+P/ufOvCxy9d5jVglLaRiTTIelHoGKCE6cDG62HYOu/3ebce6M7Z6LX6l1J9pB5PUx+f2DaMYYEGuOtNA7/ei5Ga/mibRBCehQIcN6FF6ESFOwAJBRLajj+orgYSy0u1sTCla0V4nSBrYA2H6lx8mD3qfDJ4hie7nU0YqZxy50F9f9UxXKIVSeutyIIBjWDDKv0kVpKy7OUerOaZXOW6HBohXuV74kXMUZu+MpLIkMHOrhJeo+edfhmeFuw4kCo5it6GkrOKrGs6zo1hSxWp7uuvKAPbvUrumC6sTsTxAUg4KTGq85IUnBTYI40Q9TZtzMcONtrWfIIF23/7NJyOmygBaFa4wFqHxe7j2gSWCQRv2fPwXo/AAJTeKwsUIY8OgmANHHbFVqJEeg27jbCuSaQFxWD7ms240YurTb55HBLk6JSufDl0CUbxoUgjrDB++gUb8oalroWDIb5NcZ94QER+HiTQfB11HcPDHvONnzk/n+iF+Mcri53ZbAButnfp2x87sh6RedeiUUWruYA4eonRq5+aj2I9cIrGLQaLemna1AQ+PyD2SMelBLukfR7GUc7zaSPjPJh2W/aYAJSyjM98g6ABNntdfhuf+6jRYnYFqSXZL1W1JPf92OMOfwfuXTE2K68sNwCRhcbHDLM=</xkms:Private>
        </xkms:RegisterResult>
    </soap:Body>
</soap:Envelope>'''

        x = parseSOAPRPC(xml)

    def testZeroLengthTypedArray(self):
        """
        Test that zero length typed arrays maintain thier type information when
        converted to a SOAP message.
        """
        empty_int = typedArrayType(typed="int")
        empty_int_message = buildSOAP( empty_int )
        self.assertNotEquals( re.search("xsd:int\[0\]", empty_int_message),
                               None )

if __name__ == '__main__':

    print """

    NOTE: The 'testArray' test will fail because 'referenced' elements are
    included in the return object.  This is a known shortcoming of
    the current version of SOAPpy.

    All other tests should succeed.

    """
    
    unittest.main()
