# -*- coding: latin-1 -*-
'''
index.py

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

from core.ui.webUi.webMenu import webMenu

class index(webMenu):
    '''
    This is the index for the web ui.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self ):
        webMenu.__init__(self)

    def makeMenu(self):
        # Clear the document
        self._content.zero()
        self._content.addNL(3)
        return '''
        <div id="text">
        
        <div align='left'><h3>Welcome to w3af web user interface</h3></div>
        <p>This interface allows you to configure and run a w3af scan, exploit web applications, create sessions and more!
        To get more information about the usage of w3af you can read the users guide that is available at the project site:
        <a href="http://w3af.sourceforge.net/">http://w3af.sourceforge.net/</a></p>
        
        <p>If you want to start a new w3af scan <a href="miscSettings.py">click here.</a></p>
        </div>
        '''
        self.format()
    
    def parsePOST(self, postData):
        '''
        This method is used to parse the POSTed options of the index configuration menu.
        It will configure index and set them for execution.
        '''
        return self.makeMenu()
