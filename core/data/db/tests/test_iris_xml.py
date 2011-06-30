'''
test_iris_xml.py

Copyright 2011 Andres Riancho

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



This file is a test generator for our url_object, based on the tests
defined in [0], which are basically a parsed version of WebKit's
test engine for URIs.

We DO NOT expect all tests to pass, but would like to have most of
the major ones. 

[0] https://raw.github.com/cweb/iri-tests/master/iris.xml
'''

from nose.plugins.skip import SkipTest

from xml.sax.handler import ContentHandler
from xml.sax import make_parser
import os

from core.data.parsers.urlParser import url_object


class iris_test(object):
    def __init__(self, id, base, input, expected):
        self.id = id
        self.base = base
        self.input = input
        self.expected = expected
        
        
class iris_xml_handler(ContentHandler):
    '''
    Parses stuff like:
        <tc:test id="1">
          <tc:uri>hello, world</tc:uri>
          <tc:expectedUri>hello, world</tc:expectedUri>
        </tc:test>
    
    Into iris_test objects, and stores those into iris_test_list.
    '''
    iris_test_list = []
    
    def startElement(self, name, attrs):
        return
        
        '''
        if (name == "img") :
            self.name = attrs.get("name");
        if (name == "title") :
            self.title = attrs.get("text");
        '''
            
    def endElement(self,name):
        return
    
        '''
        if (name == "img") :
            print "%8s %s" % (self.name, self.title)
            self.name = self.title = "" # just for safety
        if (name == "title") :
            pass
        '''

def run_iris(iris_test):
    expected_result = iris_test.expected
    test_id = iris_test.id
    base = iris_test.base
    
    #assert n % 2 == 0 or n % 2 == 0


def test_main():
    raise SkipTest()
 
    iris = iris_xml_handler()
    saxparser = make_parser()
    saxparser.setContentHandler(iris)

    iris_path = os.path.join('core','data','parsers','tests','iris.xml')    
    datasource = open(iris_path,"r")
    saxparser.parse(datasource)
                    
    for iris_test in iris.iris_test_list:
        yield run_iris, iris_test


