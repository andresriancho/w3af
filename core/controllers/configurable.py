'''
configurable.py

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

class configurable:
    '''
    This is mostly "an interface", this "interface" states that all classes that implement it, should
    implement the following methods :
        1. setOptions( OptionMap )
        2. getOptionsXML()
        
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def setOptions( self, OptionsMap ):
        '''
        Sets the Options given on the OptionsMap to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptionsXML()
        
        This method MUST be implemented on every configurable object. 
        
        @return: No value is returned.
        ''' 
        raise w3afException('Configurable object is not implementing required method setOptions' )
        

    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the configurable object has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/display.xsd
        
        This method MUST be implemented on every plugin. 
        
        @return: XML String
        '''
        raise w3afException('Configurable object is not implementing required method getOptionsXML' )

    def getName( self ):
        return self.__class__.__name__
        
    def getType( self ):
        return 'configurable'
