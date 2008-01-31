# -*- coding: latin-1 -*-
'''
webMenu.py

Copyright 2007 Mariano Nuñez Di Croce @ CYBSEC

This file is part of sapyto, http://www.cybsec.com/EN/research/tools/sapyto.php

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

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
import core.ui.webUi.content.htmlFile as htmlFile
import re
import cgi

# for parsing options
import xml.dom.minidom

from core.controllers.misc.parseOptions import parseXML

class webMenu:
    '''
    This class is a menu for web.
    
    @author: Mariano Nuñez Di Croce <mnunez@cybsec.com>
    '''
    def __init__( self ):
        self._content = htmlFile.htmlFile()
        self._defs = {'jscripts':['js/functions.js'], 'styles':['css/standard.css']}
        
        # Just to let all subclasses call this without importing the function
        self.parseXML = parseXML
        
    def parsePOSTedData( self, postData ):
        '''
        Parses the data sent from the browser using a POST request and returns a map that
        can be used as a parameter to a setOptions method.
        '''
        confOptions = {}
            
        for opt in postData.keys():
            res = re.findall('.*-(.*)-(.*)', opt)[0]
            optName = res[0]
            optField = res[1]
            if not optName in confOptions.keys():
                confOptions[optName] = {}
            confOptions[optName] [optField] = postData[opt][0]
        
        # Check for Boolean options
        for opt in confOptions:
            if confOptions[opt]['type'] == 'Boolean':
                if not 'default' in confOptions[opt].keys():
                    # If fails, is because checkbox was not sent, so unchecked, so False
                    confOptions[opt]['default'] = 'False'
                else:
                    confOptions[opt]['default'] = 'True'
        
        return confOptions
        
    def format(self):
        self._content.format(self._defs)

    def getMenuName(self):
        return self.__class__.__name__

    def escape( self, s ):
        return cgi.escape( s )
        
