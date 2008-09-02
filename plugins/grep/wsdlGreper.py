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
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
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
        
        if response.is_text_or_html():

            if response.getCode() == 200:
                isWsdl = False
                for wsdl_string in self._getStringsWsdl():
                    if wsdl_string in response:
                        isWsdl = True
                        break
                    
                if isWsdl:
                    i = info.info()
                    i.setName('WSDL file')
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                    i.setDesc( 'The URL: "' +  i.getURL() + '" is a Web Services Description Language page.' )
                    kb.kb.append( self , 'wsdl' , i )
                
                isDisco = False
                for disco_string in ['disco:discovery ']:
                    if disco_string in response:
                        isDisco = True
                        break
                    
                if isDisco:
                    i = info.info()
                    i.setURL( response.getURL() )
                    i.setDesc( 'The URL : ' +  i.getURL() + ' is a DISCO file that contains references to WSDLs.' )
                    kb.kb.append( self , 'disco' , i )
            
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

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
