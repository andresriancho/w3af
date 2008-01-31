'''
wsdlGreper.py

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

import core.data.parsers.htmlParser as htmlParser
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
from core.data.getResponseType import *

class wsdlGreper(baseGrepPlugin):
    '''
    Grep every page for web service definition files.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

    def _testResponse(self, request, response):
        
        if isTextOrHtml(response.getHeaders()):
            htmlString = response.getBody()
            if response.getCode() == 200:
                isWsdl = False
                for str in self._getStringsWsdl():
                    if htmlString.count(str):
                        isWsdl = True
                        break
                    
                if isWsdl:
                    i = info.info()
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.setDesc( 'The URL : ' +  i.getURL() + ' is a Web Services Description Language page.' )
                    kb.kb.append( self , 'wsdl' , i )
                
                isDisco = False
                for str in ['disco:discovery ']:
                    if htmlString.count(str):
                        isDisco = True
                        break
                    
                if isDisco:
                    i = info.info()
                    i.setURL( response.getURL() )
                    i.setDesc( 'The URL : ' +  i.getURL() + ' is a DISCO file that contains references to WSDLs.' )
                    kb.kb.append( self , 'disco' , i )
            
    def setOptions( self, OptionList ):
        pass
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '

    def _getStringsWsdl( self ):
        res = []
        
        res.append( 'xs:int' )
        res.append( 'targetNamespace' )
        res.append( 'soap:body' )
        res.append( '/s:sequence' )
        res.append( 'wsdl:' )
        res.append( 'soapAction=' )
        # This aint wsdl... but well...
        res.append( 'xmlns="urn:uddi"' )
        res.append( '<p>Hi there, this is an AXIS service!</p>' )
                
        return res
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'wsdlGreper', 'wsdl' ), 'URL' )
        self.printUniq( kb.kb.getData( 'wsdlGreper', 'disco' ), 'URL' )
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for WSDL definitions.
        
        Not all wsdls are found appending "?WSDL" to the url like discovery.wsdlFinder
        plugin does, this grep plugin will find some wsdl's that arent found by the 
        discovery plugin.
        '''
