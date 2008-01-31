# -*- coding: latin-1 -*-
'''
urlSettings.py

Copyright 2007 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

sapyto is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

sapyto is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with sapyto; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''

import core.controllers.w3afCore as core
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.webUi.webMenu import webMenu

class urlSettings(webMenu):
    '''
    This is the urlSettings configuration menu for the web ui.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self ):
        webMenu.__init__(self)
        self._w3afCore = core.wCore
        self._configurableObject = self._w3afCore.uriOpener.settings

    def makeMenu(self):
        # Clear the document
        self._content.zero()
        self._content.addNL(3)
        
        # Make a menu with all the registered plugin types
        self._content.writeFormInit( self.getMenuName() , 'POST', self.getMenuName()+'.py')
        
        # Write configurable object options
        options = self.parseXML(self._configurableObject.getOptionsXML())
        self._content.writeConfigOptions(self._configurableObject, options )
        self._content.addNL(2)
        self._content.writeSubmit('Save')
        self._content.writeFormEnd()
        self.format()
        
        return self._content.read()
        
    def parsePOST(self, postData):
        '''
        This method is used to parse the POSTed options of the urlSettings configuration menu.
        It will configure urlSettings.
        '''
        # Clear the document
        self._content.zero()
        
        confOptions = self.parsePOSTedData( postData )      
        
        try:
            self._configurableObject.setOptions(confOptions)
        except w3afException, w3:
            self._content.writeError( str(w3) )
        else:
            self._content.writeMessage('<div id="text">URL settings successfully configured.</div>')
            self._content.writeNextBackPage('Session creation', 'session.py', 'Misc settings', 'miscSettings.py')
        
        return self._content.read()
