#!/usr/bin/env python

import sys, unittest
sys.path.insert(1, "..")
from SOAPpy import *
Config.debug=1

class ClientTestCase(unittest.TestCase):
    def testParseRules(self):
        x = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <soap:Body
         soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
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
         """

        def negfloat(x):
            return float(x) * -1.0

        # parse rules
        pr = {'SomeMethod':
               {'Result':
                 {
                  'Book':   {'title':'string'},
                  'Person': {'age':'int',
                             'height':negfloat}
                  }
               }
             } 
        y = parseSOAPRPC(x, rules=pr)
        
        assert y.Result.Person.age == 49
        assert y.Result.Person.height == -5.5


        x = '''<SOAP-ENV:Envelope
         SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
         xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
         xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
         xmlns:xsd="http://www.w3.org/1999/XMLSchema"
         xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">
          <SOAP-ENV:Body>
            <Bounds>
              <param>
                <item>12</item>
                <item>23</item>
                <item>0</item>
                <item>-31</item>
              </param>
              <param1 xsi:null="1"></param1>
            </Bounds>
          </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>
        '''

        
        # parse rules
        pr = {'Bounds':
              {'param': 'arrayType=string[]',
               }
              }
        
        pr2 = {'Bounds':
               {'param': 'arrayType=int[4]',
                }
               }
        
        y = parseSOAPRPC(x, rules=pr)
        assert y.param[1]=='23'

        y = parseSOAPRPC(x, rules=pr2)
        assert y.param[1]==23

        x = '''<SOAP-ENV:Envelope
        SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
        xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
        xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsd="http://www.w3.org/1999/XMLSchema"
        xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">

          <SOAP-ENV:Body>
            <Bounds>
              <param>
                <item xsi:type="xsd:int">12</item>
                <item xsi:type="xsd:string">23</item>
                <item xsi:type="xsd:float">0</item>
                <item xsi:type="xsd:int">-31</item>
              </param>
              <param1 xsi:null="1"></param1>
            </Bounds>
            </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>
        '''

        pr = {'Bounds':
              {'param': 'arrayType=ur-type[]'
               }
              }
        y = parseSOAPRPC(x, rules=pr)
        assert y.param[0]==12
        assert y.param[1]=='23'
        assert y.param[2]==float(0)
        assert y.param[3]==-31

        # Try the reverse, not implemented yet.

    def testBuildObject(self):

        class Book(structType):
            def __init__(self):
                self.title = "Title of a book"

        class Person(structType):
            def __init__(self):
                self.age = "49"
                self.height = "5.5"

        class Library(structType):
            def __init__(self):
                self._name = "Result"
                self.Book = Book()
                self.Person = Person()

        obj = Library()
        
        x = buildSOAP( kw={'Library':obj} ) 

        print(x)

if __name__ == '__main__':
    unittest.main()
